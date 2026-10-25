import hashlib,json,sys,time
from pathlib import Path
req=json.loads(sys.stdin.read(65536));root=Path(req['directory']);assert str(root).endswith('/experiments/retention-pilot-v1/results/peano-hydra/qwen3-1.7b-authority-primitive-retention-pilot-v1')
beg=time.monotonic();observed={}
assert len(req['files'])==11
for name,wanted in req['files'].items():
 rel=Path(name);assert not rel.is_absolute() and '..'not in rel.parts
 path=root/rel;assert path.is_file() and not path.is_symlink() and path.stat().st_size<100*1024*1024
 before=path.stat();raw=path.read_bytes();h=hashlib.sha256(raw).hexdigest();after=path.stat()
 assert h==wanted and before.st_size==after.st_size==len(raw) and before.st_mtime_ns==after.st_mtime_ns
 observed[name]={'sha256':h,'bytes':len(raw)}
print(json.dumps({'completed':True,'read_only':True,'directory':str(root),'files':observed,'elapsed_seconds':time.monotonic()-beg,'model_loaded':False}))
