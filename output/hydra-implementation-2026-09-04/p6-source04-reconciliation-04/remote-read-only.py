
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

