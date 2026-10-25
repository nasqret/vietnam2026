
import hashlib,json,os,signal,sys,tarfile,time
from pathlib import Path
os.umask(0o077)
signal.alarm(180)
started=time.monotonic()
header=sys.stdin.buffer.readline(1024*1024+1)
assert len(header)<=1024*1024 and header.endswith(b'\n')
request=json.loads(header)
manifest=request['manifest']
directory=Path(request['directory'])
assert str(directory)=='/net/scratch/hscra/plgrid/plgnasqret/codex-control/projects/peano-lab-training/experiments/hydra-practical-v1-20260904/bundles/source-data-03'
assert manifest['archive_bytes']==10250626 and manifest['archive_sha256']=='382f5812ffbefff894ea06b1e9444d5fae8199e9726f5a39d8d482fc2c998eb6'
assert manifest['expanded_bytes']<128*1024*1024 and manifest['file_count']<1300
directory.mkdir(parents=True,exist_ok=False)
archive=directory/'source-data.tar.gz'
remaining=manifest['archive_bytes'];digest=hashlib.sha256()
with archive.open('xb') as out:
 while remaining:
  block=sys.stdin.buffer.read(min(1024*1024,remaining))
  assert block,'Premature upload EOF'
  out.write(block);digest.update(block);remaining-=len(block)
 assert not sys.stdin.buffer.read(1),'Trailing upload bytes'
assert digest.hexdigest()==manifest['archive_sha256']
source=directory/'source';source.mkdir()
observed=set();total=0
with tarfile.open(str(archive),'r:gz') as tar:
 for item in tar:
  assert item.name not in observed and item.name in manifest['files']
  observed.add(item.name);pin=manifest['files'][item.name]
  path=Path(item.name)
  assert item.isfile() and not path.is_absolute() and '..' not in path.parts and item.size==pin['bytes']
  total+=item.size;assert total<=manifest['expanded_bytes']
  raw=tar.extractfile(item).read(item.size+1)
  assert len(raw)==pin['bytes'] and hashlib.sha256(raw).hexdigest()==pin['sha256']
  target=source/path;target.parent.mkdir(parents=True,exist_ok=True)
  with target.open('xb') as out:out.write(raw)
assert observed==set(manifest['files']) and total==manifest['expanded_bytes']
(directory/'manifest.json').write_text(json.dumps(manifest,sort_keys=True,indent=2)+'\n')
record={'schema':'hydra-source-transfer-receipt-v1','directory':str(directory),'source':str(source),
 'archive_sha256':digest.hexdigest(),'verified_files':len(observed),'verified_bytes':total,
 'elapsed_seconds':time.monotonic()-started,'gpu_allocations':0,'automatic_retry':False}
(directory/'transfer-receipt.json').write_text(json.dumps(record,indent=2)+'\n')
print(json.dumps(record),flush=True)
