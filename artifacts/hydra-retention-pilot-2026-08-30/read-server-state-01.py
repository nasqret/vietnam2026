"""One bounded read-only Helios readiness observation for the new pilot."""
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import resource
import shlex
import subprocess
import sys
import time

ARCHIVE = Path('/Users/bnaskrecki/codex/peano/artifacts/hydra-retention-pilot-2026-08-30')
resource.setrlimit(resource.RLIMIT_CPU, (15, 15))
resource.setrlimit(resource.RLIMIT_FSIZE, (1024 * 1024, 1024 * 1024))
program = r'''
import datetime,hashlib,json,os,resource,stat,subprocess
from pathlib import Path
resource.setrlimit(resource.RLIMIT_CPU,(10,10))
resource.setrlimit(resource.RLIMIT_AS,(256*1024**2,256*1024**2))
resource.setrlimit(resource.RLIMIT_FSIZE,(0,0))
p=Path('/net/scratch/hscra/plgrid/plgnasqret/codex-control/projects/peano-lab-training')
checks={}
files={
 'old_model_manifest':p/'_deploy/hydra-search-v2/model/manifest.json',
 'new_model_manifest':p/'experiments/frontier-training-v1/results/peano-hydra/qwen3-1.7b-authority-primitive-v28-f64b5f100c9c-frontier-training-v1/manifest.json',
 'original_diagnostic_head':p/'experiments/frontier-diagnostic-v1/results/peano-hydra/evaluations/frontier-diagnostic-v1/checkpoint/HEAD.json',
 'original_diagnostic_ledger':p/'experiments/frontier-diagnostic-v1/logs/hydra-frontier-diagnostic-v1.jsonl',
}
for name,path in files.items():
 s=path.lstat()
 assert stat.S_ISREG(s.st_mode) and s.st_nlink==1 and s.st_size<4*1024**2
 raw=path.read_bytes()
 checks[name]={'path':str(path),'bytes':len(raw),'sha256':hashlib.sha256(raw).hexdigest()}
checks['old_source_present']=(p/'_deploy/hydra-search-v2/origin-source').is_dir()
checks['frontier_source_present']=(p/'experiments/frontier-training-v1/training/peano_hydra/posttrain.py').is_file()
checks['new_destination_absent']=not os.path.lexists(p/'experiments/retention-pilot-v1')
checks['runtime_python_executable']=os.access(p/'.venv-helios/bin/python',os.X_OK)
checks['offline_cache_present']=(p/'.cache/huggingface').is_dir()
checks['available_bytes']=os.statvfs(p).f_bavail*os.statvfs(p).f_frsize
q=subprocess.run(['squeue','-h','-u','plgnasqret','-o','%i|%Z|%j|%T|%b'],stdin=subprocess.DEVNULL,stdout=subprocess.PIPE,stderr=subprocess.PIPE,timeout=10)
assert q.returncode==0 and len(q.stdout)<65536 and len(q.stderr)<4096
checks['active_jobs']=q.stdout.decode().splitlines()
result={'observed_at_utc':datetime.datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%SZ'),'checks':checks,'read_only':True,'model_loaded':False,'native_proof_executed':False,'scheduler_mutation_performed':False}
raw=json.dumps(result,sort_keys=True)
assert len(raw.encode())<65536
print(raw)
'''
command = ['/usr/bin/ssh', '-T', '-o', 'BatchMode=yes', '-o', 'ConnectTimeout=15',
           '-o', 'ServerAliveInterval=10', '-o', 'ServerAliveCountMax=2',
           '-o', 'ForwardAgent=no', '-o', 'ClearAllForwardings=yes', '-o', 'StrictHostKeyChecking=yes',
           '-o', 'UpdateHostKeys=no', '-o', 'ControlMaster=no', '-o', 'ControlPath=none', '--',
           'plgnasqret@helios.cyfronet.pl', '/usr/bin/python3.9 -I -B -c ' + shlex.quote(program)]
started = time.monotonic()
completed = subprocess.run(command, stdin=subprocess.DEVNULL, stdout=subprocess.PIPE,
                           stderr=subprocess.PIPE, timeout=45)
assert len(completed.stdout) <= 65536 and len(completed.stderr) <= 8192
record = {'schema': 'peano-hydra-retention-server-readiness-v1', 'recorded_at_utc': datetime.now(timezone.utc).isoformat(),
          'returncode': completed.returncode, 'stdout': completed.stdout.decode(), 'stderr': completed.stderr.decode(),
          'read_only': True, 'automatic_retry': False, 'wall_seconds': time.monotonic()-started,
          'helper_sha256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
          'remote_program_sha256': hashlib.sha256(program.encode()).hexdigest()}
if completed.returncode == 0:
    result = json.loads(record['stdout'])
    checks = result['checks']
    assert checks['old_model_manifest']['sha256']=='172a6928710192c5348dcd7b04f71e6d4d3f75dfa1ab0f7f5add601769704a7c'
    assert checks['new_model_manifest']['sha256']=='5795d5a3d70f781f56f81e83c2295c887d0949795924f4208f45d26a3ef89b68'
    assert checks['original_diagnostic_head']['sha256']=='1a8fc0aff6fdc67a91bb9c01fd486f9273e1994c047588f8ef8d958f3d70c407'
    assert checks['original_diagnostic_ledger']['sha256']=='10736f4b83947a315a5fe04cebde7961871e413073dbec51ef227c74e716132c'
    record['result'] = result
raw=(json.dumps(record,indent=2,sort_keys=True)+'\n').encode()
with (ARCHIVE/'server-readiness-01.json').open('xb') as stream:
    stream.write(raw)
print(json.dumps({'receipt':str(ARCHIVE/'server-readiness-01.json'),'bytes':len(raw),'sha256':hashlib.sha256(raw).hexdigest(),'result':record.get('result'),'returncode':completed.returncode},sort_keys=True))
raise SystemExit(completed.returncode)
