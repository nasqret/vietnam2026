import hashlib,json,os,stat
from pathlib import Path
p=Path('/net/scratch/hscra/plgrid/plgnasqret/codex-control/projects/peano-lab-training/experiments/hydra-practical-v1-20260904/cpu-fixture-01')
r={'uid':os.getuid(),'read_only':True,'files':{}}
assert os.getuid()==105923
for name in ('reservation.json','reservation.sha256','sbatch.stdout.txt','sbatch.stderr.txt','sbatch.execution.json','held-inspect.stdout.txt','held-inspect.stderr.txt','held-inspect.execution.json'):
 q=p/name;i=q.lstat();assert stat.S_ISREG(i.st_mode) and i.st_nlink==1 and i.st_size<=65536
 raw=q.read_bytes();assert len(raw)==i.st_size
 r['files'][name]={'bytes':len(raw),'sha256':hashlib.sha256(raw).hexdigest(),'text':raw.decode()}
print(json.dumps(r))
