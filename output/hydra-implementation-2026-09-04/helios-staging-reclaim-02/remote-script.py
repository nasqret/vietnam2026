
import hashlib,json,os,signal,subprocess,sys,time
from pathlib import Path
signal.alarm(90)
started=time.monotonic()
request=json.loads(sys.stdin.buffer.read(2*1024*1024))
allowed={'/net/scratch/hscra/plgrid/plgnasqret/codex-control/projects/peano-lab-training/experiments/hydra-practical-v1-20260904/bundles/source-data-03'}
assert {row['directory'] for row in request['targets']}==allowed
queue=subprocess.run(['squeue','-h','-u',str(os.getuid()),'-o','%i|%j'],stdout=subprocess.PIPE,stderr=subprocess.PIPE,universal_newlines=True,timeout=5)
assert queue.returncode==0 and len(queue.stdout.encode())<=16384
assert not any('hydra-p6' in line or 'hydra-p7' in line for line in queue.stdout.splitlines()),'A Hydra input consumer is still scheduled'
prepared=[]
for target in request['targets']:
 directory=Path(target['directory']);source=directory/'source';manifest=target['manifest']
 assert directory.resolve()==directory and source.is_dir() and not source.is_symlink()
 archive=directory/'source-data.tar.gz'
 assert archive.is_file() and not archive.is_symlink()
 raw=archive.read_bytes()
 assert len(raw)==manifest['archive_bytes'] and hashlib.sha256(raw).hexdigest()==manifest['archive_sha256']
 files=[];folders=[];observed=set();total=0
 for parent,names,leaves in os.walk(source,followlinks=False):
  parent=Path(parent)
  for name in names:
   folder=parent/name;assert not folder.is_symlink();folders.append(folder)
  for name in leaves:
   path=parent/name;relative=path.relative_to(source).as_posix()
   assert not path.is_symlink() and relative in manifest['files']
   pin=manifest['files'][relative];data=path.read_bytes()
   assert len(data)==pin['bytes'] and hashlib.sha256(data).hexdigest()==pin['sha256'],relative
   observed.add(relative);files.append(path);total+=len(data)
 assert 0<len(files)<=manifest['file_count']<1300
 if not target['partial']:assert observed==set(manifest['files'])
 prepared.append((target,source,files,folders,total,sorted(observed)))
record={'schema':'hydra-archived-input-retirement-v1','completed':False,'targets':[],
 'scope':'Only verified extracted copies; exact archives/receipts/model files and unrelated projects remain',
 'gpu_allocations':0,'automatic_retry':False}
print(json.dumps({'phase':'all_before_unlink_checks_passed','targets':[{'directory':t['directory'],'files':len(f),'directories':len(d)+1,'bytes':n,'archive_sha256':t['manifest']['archive_sha256']}for t,s,f,d,n,o in prepared]}),flush=True)
for target,source,files,folders,total,observed in prepared:
 for path in files:path.unlink()
 for folder in sorted(folders,key=lambda p:len(p.parts),reverse=True):folder.rmdir()
 source.rmdir()
 record['targets'].append({'directory':target['directory'],'removed_extracted_files':len(files),
  'removed_empty_directories':len(folders)+1,'removed_extracted_bytes':total,
  'recoverable_archive_sha256':target['manifest']['archive_sha256'],
  'archive_preserved':(Path(target['directory'])/'source-data.tar.gz').is_file(),
  'observed_names_sha256':hashlib.sha256(json.dumps(observed,separators=(',',':')).encode()).hexdigest()})
record.update(completed=True,elapsed_seconds=time.monotonic()-started)
print(json.dumps(record),flush=True)
