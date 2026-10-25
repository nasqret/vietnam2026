
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

