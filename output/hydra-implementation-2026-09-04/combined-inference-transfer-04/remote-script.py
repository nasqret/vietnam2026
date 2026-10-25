
import base64,hashlib,json,os,resource,signal,stat,subprocess,sys,time
from pathlib import Path
os.umask(0o077)
resource.setrlimit(resource.RLIMIT_CPU,(60,75))
resource.setrlimit(resource.RLIMIT_AS,(512*1024**2,512*1024**2))
resource.setrlimit(resource.RLIMIT_FSIZE,(128*1024**2,128*1024**2))
resource.setrlimit(resource.RLIMIT_CORE,(0,0))
signal.alarm(120);began=time.monotonic()
assert os.getuid()==105923
campaign=Path('/net/scratch/hscra/plgrid/plgnasqret/codex-control/projects/peano-lab-training/experiments/hydra-practical-v1-20260904')
old=campaign/'bundles/combined-source-03'
directory=campaign/'bundles/combined-source-04'
metadata_pins={
 'manifest.json':(253561,'4beeb386a118229b4e3fa9b751d7a4a560853252ab3103cff661a48dc2eb9f0e'),
 'paired-source-pins.json':(126170,'d32c30a437070986df9777bf97dbb56f362e720d63ba32be16d8b728155ecf9d'),
 'teacher-source-pins.json':(108200,'e76da7607ea7be7681c30a5583bfb71c998aab7660754e28cb0c4cb61f5b3d7a'),
 'student-source-pins.json':(101298,'8e55a8f20c5aaf8893d5850c008d0a54408cac9600d2827de4b6eeb95f2c887c'),
 'teacher-paired-source-pins.json':(126761,'d184338a35b8aebde03a5edad16995038717502d4d84924da7f4750e36247ce9')}
def digest(raw):return hashlib.sha256(raw).hexdigest()
def canonical(value):return json.dumps(value,sort_keys=True,separators=(',',':'),ensure_ascii=False,allow_nan=False).encode()
def stamp(s):return(s.st_dev,s.st_ino,s.st_mode,s.st_uid,s.st_nlink,s.st_size,s.st_mtime_ns,s.st_ctime_ns)
def read_file(path,maximum):
 assert path.is_file() and not path.is_symlink()
 before=path.lstat();assert stat.S_ISREG(before.st_mode) and before.st_uid==105923 and before.st_size<=maximum
 fd=os.open(str(path),os.O_RDONLY|os.O_NOFOLLOW)
 with os.fdopen(fd,'rb')as stream:
  assert stamp(os.fstat(stream.fileno()))==stamp(before)
  raw=stream.read(maximum+1)
  assert stamp(os.fstat(stream.fileno()))==stamp(before)
 assert len(raw)==before.st_size and stamp(path.lstat())==stamp(before)
 return raw
def source_path(root,name):
 rel=Path(name)
 assert rel.parts and not rel.is_absolute() and str(rel)==name and '..'not in rel.parts and '.'not in rel.parts
 path=root;assert path.is_dir() and not path.is_symlink()
 for part in rel.parts:
  path=path/part;assert not path.is_symlink()
 return path
def write_file(path,raw):
 path.parent.mkdir(parents=True,exist_ok=True)
 with path.open('xb')as stream:stream.write(raw)
 path.chmod(0o444)
 assert path.lstat().st_nlink==1 and read_file(path,len(raw))==raw
request_raw=sys.stdin.buffer.read(2*1024*1024+1)
assert len(request_raw)<=2*1024*1024
request=json.loads(request_raw)
assert set(request)=={'schema','authority','payloads','automatic_retry'}
assert request['schema']=='hydra-combined-inference-source-copy-request-v4'
assert request['authority']=='HYDRA_EXPERIMENT_AUTHORITY.md' and request['automatic_retry']is False
assert isinstance(request['payloads'],dict) and len(request['payloads'])==3
payloads={name:base64.b64decode(value,validate=True)for name,value in request['payloads'].items()}
uploaded_metadata={'manifest.json','paired-source-pins.json'}
for name in uploaded_metadata:
 size,sha=metadata_pins[name];assert len(payloads[name])==size and digest(payloads[name])==sha
manifest=json.loads(payloads['manifest.json'])
assert digest(canonical(manifest))=='aa001fceb6eaefcf3073287f8cb8a8efacffc245fe524759ad95a0d34571c9dd'
assert manifest['schema']=='hydra-combined-inference-source-v4' and manifest['runtime_destination']=='combined-source-04/source'
assert manifest['automatic_launch']is False and manifest['automatic_retry']is False
assert manifest['native_case_search_data_unchanged']is True and manifest['original_source_inputs_unchanged']is True
assert len(manifest['files'])==manifest['file_count']==1325 and manifest['expanded_bytes']==112082345
assert manifest['archive_sha256']=='63bad7bea869d8ee279124ab6ec00a66c5dd5cc399f4e7d4a68c5bd0189479a4'
assert manifest['provider_sha256']=='cc279710866146414c439e17935915f28d7dda7a44df20aa5d7e6bcd87994c44'
assert len(manifest['changed_files'])==manifest['changed_file_count']==1
changes=manifest['changed_files'];expected_payloads=uploaded_metadata|{'source/'+name for name in changes}
assert set(payloads)==expected_payloads and sum(len(raw)for raw in payloads.values())==423394
assert old.is_dir() and not old.is_symlink() and directory.parent.is_dir() and not directory.parent.is_symlink()
old_raw=read_file(old/'manifest.json',1024*1024);original=json.loads(old_raw)
assert digest(old_raw)=='bff0239d9e0c74e088118a271907da887d009acad3e3b21eca4534c1da855c08'
assert digest(canonical(original))=='9b73388872811477057ff6f3ddff9e5b54020b12c22059d12519594bea15da62'
assert manifest['parent_manifest_sha256']=='bff0239d9e0c74e088118a271907da887d009acad3e3b21eca4534c1da855c08'
assert original['archive_sha256']==manifest['parent_archive_sha256']=='719e4ec3e602b9617e003358721281dd2b35690b2fcccd6ee98f4e576a75ff9e'
assert len(original['files'])==original['file_count']==1325 and original['expanded_bytes']==112070657
assert set(original['files'])==set(manifest['files'])
assert {name for name in manifest['files']if manifest['files'][name]!=original['files'][name]}==set(changes)
for name,change in changes.items():
 assert change['before']==original['files'][name] and change['after']==manifest['files'][name]
 raw=payloads['source/'+name];pin=change['after']
 assert len(raw)==pin['bytes']and digest(raw)==pin['sha256']
for name,pin in manifest['files'].items():
 assert type(pin['bytes'])is int and 0<=pin['bytes']<=128*1024**2
 rel=Path(name);assert rel.parts and not rel.is_absolute() and str(rel)==name and '..'not in rel.parts and '.'not in rel.parts
 assert all(str(parent)not in manifest['files']for parent in rel.parents if str(parent)!='.')
metadata={name:(payloads[name]if name in uploaded_metadata else read_file(old/name,pin[0]))for name,pin in metadata_pins.items()}
for name,(size,sha)in metadata_pins.items():assert len(metadata[name])==size and digest(metadata[name])==sha
scopes={}
for kind,pin in manifest['source_maps'].items():
 name=kind+'-source-pins.json';raw=metadata[name];scope=json.loads(raw)
 assert {'bytes':len(raw),'sha256':digest(raw)}=={key:pin[key]for key in ('bytes','sha256')}
 assert len(scope)==pin['files']and digest(canonical(scope))==pin['content_sha256']
 if kind=='teacher':
  assert all(manifest['files'][name]['sha256']==value for name,value in scope.items())
 else:
  assert all(manifest['files'][name]==value for name,value in scope.items())
 scopes[kind]=pin
assert set(scopes)=={'paired','teacher','student','teacher-paired'}
assert not directory.exists() and not directory.is_symlink()
quota=subprocess.run(['/usr/bin/lfs','quota','-q','-u',str(os.getuid()),str(campaign)],stdout=subprocess.PIPE,stderr=subprocess.PIPE,universal_newlines=True,timeout=10)
assert quota.returncode==0 and len(quota.stdout)<16384 and len(quota.stderr)<16384
numbers=quota.stdout.splitlines()[-1].split()[-8:]
used=int(numbers[4].rstrip('*'));limit=int(numbers[6])
parents={str(parent)for name in manifest['files']for parent in Path(name).parents if str(parent)!='.'}
required=1325+len(parents)+256
assert 0<=used<=limit and limit-used>=required,'Exact copy and result reserve exceed the remaining file quota'
directory.mkdir(exist_ok=False);source=directory/'source';source.mkdir()
total=0;old_total=0
for name in sorted(original['files']):
 pin=original['files'][name];raw=read_file(source_path(old/'source',name),pin['bytes'])
 assert len(raw)==pin['bytes']and digest(raw)==pin['sha256']
 old_total+=len(raw);assert old_total<=original['expanded_bytes']
 replacement=payloads['source/'+name]if name in changes else raw;expected=manifest['files'][name]
 assert len(replacement)==expected['bytes']and digest(replacement)==expected['sha256']
 write_file(source/name,replacement);total+=len(replacement);assert total<=manifest['expanded_bytes']
assert total==manifest['expanded_bytes']and old_total==original['expanded_bytes']
observed=set()
for path in source.rglob('*'):
 assert not path.is_symlink()
 if path.is_file():
  name=path.relative_to(source).as_posix();assert name in manifest['files']
  pin=manifest['files'][name];raw=read_file(path,pin['bytes'])
  assert path.lstat().st_nlink==1 and len(raw)==pin['bytes']and digest(raw)==pin['sha256'];observed.add(name)
 else:assert path.is_dir()
assert observed==set(manifest['files'])
for name,pin in original['files'].items():
 raw=read_file(source_path(old/'source',name),pin['bytes'])
 assert len(raw)==pin['bytes']and digest(raw)==pin['sha256']
assert read_file(old/'manifest.json',1024*1024)==old_raw
for name in set(metadata_pins)-uploaded_metadata:assert read_file(old/name,metadata_pins[name][0])==metadata[name]
for name in metadata_pins:write_file(directory/name,metadata[name])
for path in source.rglob('*'):
 if path.is_dir():path.chmod(0o555)
source.chmod(0o555)
record={'schema':'hydra-combined-inference-source-copy-receipt-v4','completed':True,'directory':str(directory),'source':str(source),
 'derived_from_source':str(old/'source'),'manifest_sha256':metadata_pins['manifest.json'][1],
 'manifest_content_sha256':digest(canonical(manifest)),'manifest_raw_bytes_preserved':True,
 'parent_remote_manifest_sha256':digest(old_raw),'parent_manifest_content_sha256':digest(canonical(original)),
 'parent_local_manifest_sha256':manifest['parent_manifest_sha256'],'source_maps':scopes,
 'provider_sha256':manifest['provider_sha256'],'provider_profile':manifest['provider_profile'],
 'verified_files':len(observed),'verified_bytes':total,'unchanged_files':1324,'changed_files':sorted(changes),
 'uploaded_payload_files':len(payloads),'copied_unchanged_metadata_files':sorted(set(metadata_pins)-uploaded_metadata),'uploaded_payload_bytes':sum(len(v)for v in payloads.values()),
 'wire_payload_bytes':len(request_raw),'archive_bytes_uploaded':0,'remote_archive_available':False,
 'local_reference_archive_sha256':manifest['archive_sha256'],'old_whitelisted_sources_unchanged':True,
 'non_whitelisted_files_copied':0,'saved_artifact_files_read':0,'hardlinks_created':0,
 'source_scope':'sealed inference/teacher/student helper source; ordinary P6 training path not admitted',
 'application_executions':0,'gpu_allocations':0,'model_calls':0,'native_runs':0,'scheduler_queries':0,
 'automatic_retry':False,'elapsed_seconds':time.monotonic()-began,
 'inode_quota_before':{'used':used,'limit':limit,'required_with_reserve':required}}
write_file(directory/'transfer-receipt.json',json.dumps(record,sort_keys=True,indent=2).encode()+b'\n')
signal.alarm(0)
print(json.dumps(record),flush=True)
