
import hashlib,json,os,shutil,signal,subprocess,sys,tarfile,time
from pathlib import Path
os.umask(0o077);signal.alarm(120);started=time.monotonic()
request=json.loads(sys.stdin.buffer.read(1024*1024));manifest=request['manifest']
campaign=Path('/net/scratch/hscra/plgrid/plgnasqret/codex-control/projects/peano-lab-training/experiments/hydra-practical-v1-20260904')
original=campaign/'bundles/source-data-04/source-data.tar.gz'
directory=campaign/'bundles/source-data-05'
assert not directory.exists() and original.is_file() and not original.is_symlink()
assert manifest['archive_sha256']=='3afd1d93160c1695cc0f5bcc4030b77db2944e77178be532c02f26c564f03b73' and manifest['archive_bytes']==10256916
assert manifest['file_count']==1206 and manifest['expanded_bytes']==108045238
raw=original.read_bytes();assert len(raw)==manifest['archive_bytes'] and hashlib.sha256(raw).hexdigest()==manifest['archive_sha256']
quota=subprocess.run(['/usr/bin/lfs','quota','-q','-u',str(os.getuid()),str(campaign)],stdout=subprocess.PIPE,stderr=subprocess.PIPE,universal_newlines=True,timeout=10)
assert quota.returncode==0 and len(quota.stdout)<16384
fields=quota.stdout.splitlines()[-1].split();assert len(fields)>=8
numbers=fields[-8:];used=int(numbers[4].rstrip('*'));limit=int(numbers[6])
parents={str(parent)for name in manifest['files'] for parent in Path(name).parents if str(parent)!='.'}
required=manifest['file_count']+len(parents)+132
assert limit-used>=required,'Insufficient inode quota for this exact extraction plus output reserve'
directory.mkdir(exist_ok=False);archive=directory/'source-data.tar.gz'
shutil.copyfile(str(original),str(archive))
source=directory/'source';source.mkdir()
observed=set();total=0
with tarfile.open(str(archive),'r:gz')as tar:
 for item in tar:
  assert item.name not in observed and item.name in manifest['files']
  observed.add(item.name);pin=manifest['files'][item.name];path=Path(item.name)
  assert item.isfile() and not path.is_absolute() and '..' not in path.parts and item.size==pin['bytes']
  total+=item.size;assert total<=manifest['expanded_bytes']
  data=tar.extractfile(item).read(item.size+1)
  assert len(data)==pin['bytes'] and hashlib.sha256(data).hexdigest()==pin['sha256']
  target=source/path;target.parent.mkdir(parents=True,exist_ok=True)
  with target.open('xb')as stream:stream.write(data)
  target.chmod(0o444)
assert observed==set(manifest['files']) and total==manifest['expanded_bytes']
(directory/'manifest.json').write_text(json.dumps(manifest,sort_keys=True,indent=2)+'\n')
record={'schema':'hydra-source-transfer-receipt-v1','directory':str(directory),'source':str(source),
 'archive_sha256':manifest['archive_sha256'],'verified_files':len(observed),'verified_bytes':total,
 'elapsed_seconds':time.monotonic()-started,'gpu_allocations':0,'automatic_retry':False,
 'origin_archive':str(original),'network_payload_bytes':0,'inode_quota_before':{'used':used,'limit':limit,'required_with_reserve':required}}
(directory/'transfer-receipt.json').write_text(json.dumps(record,indent=2)+'\n')
print(json.dumps(record),flush=True)
