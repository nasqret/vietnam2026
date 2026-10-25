"""Stage one inference derivative from already staged, whitelisted source files.

Upload only the reviewed provider, exact manifest and runtime source map. Copy
the other original source files on Helios; never copy saved adapter outputs,
modify old trees, allocate a job or execute application/model code.
"""
from pathlib import Path
import argparse
import ast
import base64
import hashlib
import json
import shlex
import subprocess
import time

from stage_p6_remote import SSH
from p6_smoke_transport import run_ssh

HERE = Path(__file__).resolve().parent
BUNDLE = HERE / "p6-source-bundle-08"
OUT = HERE / "p6-inference-transfer-01"
PROVIDER = "hydra-playground/experimental_model.py"
SEAL_SHA = "1af7699077b2d9c77adeb277969d8c9c64fee52b66e1c333cf29c132864b9b89"
ACTUAL_SHA = "01c2456df243246ee4ecd0b19b7914914b955b74e20cb8eaee59fdb6eca8008f"
PINS = {
    "manifest.json": {"bytes": 230520, "sha256": "baa6c45db4fb01806a36aa188508e7cca9517a41934e5ad2f46739873722e1ff"},
    "controller-source-pins.json": {"bytes": 99834, "sha256": "d981ef26de980dc983b3f0efd0885d46aaf2a08767e34b924e83632928f8cb5f"},
    "provider.py": {"bytes": 50020, "sha256": "cc279710866146414c439e17935915f28d7dda7a44df20aa5d7e6bcd87994c44"},
}

REMOTE = r'''
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
old=campaign/'bundles/source-data-07'
directory=campaign/'bundles/source-data-09'
provider='hydra-playground/experimental_model.py'
pins={
 'manifest.json':(230520,'baa6c45db4fb01806a36aa188508e7cca9517a41934e5ad2f46739873722e1ff'),
 'controller-source-pins.json':(99834,'d981ef26de980dc983b3f0efd0885d46aaf2a08767e34b924e83632928f8cb5f'),
 'provider.py':(50020,'cc279710866146414c439e17935915f28d7dda7a44df20aa5d7e6bcd87994c44')}
def digest(raw):return hashlib.sha256(raw).hexdigest()
def canonical(value):return json.dumps(value,sort_keys=True,separators=(',',':'),ensure_ascii=False,allow_nan=False).encode()
def stamp(s):return(s.st_dev,s.st_ino,s.st_size,s.st_mtime_ns,s.st_ctime_ns)
def read_file(path,maximum):
 assert path.is_file() and not path.is_symlink()
 before=path.lstat();assert stat.S_ISREG(before.st_mode) and before.st_uid==105923 and before.st_size<=maximum
 with path.open('rb')as stream:
  assert stamp(os.fstat(stream.fileno()))==stamp(before)
  raw=stream.read(maximum+1)
  assert stamp(os.fstat(stream.fileno()))==stamp(before)
 assert len(raw)==before.st_size and stamp(path.lstat())==stamp(before)
 return raw
def source_path(root,name):
 rel=Path(name)
 assert not rel.is_absolute() and str(rel)==name and '..'not in rel.parts and '.'not in rel.parts
 path=root
 assert path.is_dir() and not path.is_symlink()
 for part in rel.parts:
  path=path/part;assert not path.is_symlink()
 return path
def write_file(path,raw):
 path.parent.mkdir(parents=True,exist_ok=True)
 with path.open('xb')as stream:stream.write(raw)
 path.chmod(0o444)
 assert read_file(path,len(raw))==raw
request_raw=sys.stdin.buffer.read(1024*1024+1)
assert len(request_raw)<=1024*1024
request=json.loads(request_raw)
assert set(request)=={'schema','authority','payloads','automatic_retry'}
assert request['schema']=='hydra-inference-source-copy-request-v1' and request['authority']=='HYDRA_EXPERIMENT_AUTHORITY.md'
assert request['automatic_retry']is False and set(request['payloads'])==set(pins)
payloads={name:base64.b64decode(value,validate=True)for name,value in request['payloads'].items()}
for name,(size,sha)in pins.items():assert len(payloads[name])==size and digest(payloads[name])==sha
manifest=json.loads(payloads['manifest.json']);scope=json.loads(payloads['controller-source-pins.json'])
old_raw=read_file(old/'manifest.json',1024*1024);original=json.loads(old_raw)
assert digest(canonical(original))=='0e87d1cf37512e71b02a01adb0e79bbda50c3ee155d5dbb74113b6fee3de7b5d'
assert manifest['inference_only']is True and manifest['training_execution_allowed']is False
assert len(manifest['files'])==manifest['file_count']==1206 and manifest['expanded_bytes']==108054509
assert len(original['files'])==1206 and set(original['files'])==set(manifest['files'])
assert {name for name in manifest['files']if manifest['files'][name]!=original['files'][name]}=={provider}
assert original['files'][provider]['sha256']=='7bacd4f97272093873db76ea7b2178e1074ca3ff5f2ef88b4e411933c131580f'
assert manifest['files'][provider]=={'bytes':pins['provider.py'][0],'sha256':pins['provider.py'][1]}
assert len(scope)==585 and digest(canonical(scope))=='85dadd08b91c9678fa8be1cf9624a82a5e0470b1c29f5a2f8cc25c7716a76f55'
assert all(manifest['files'][name]==pin for name,pin in scope.items())
assert manifest['archive_sha256']=='186b7eae5bc6388044a2618353f014f95486e86ed2cd1483978d177570525ddc'
assert not directory.exists() and not directory.is_symlink()
assert old.is_dir() and not old.is_symlink() and directory.parent.is_dir() and not directory.parent.is_symlink()
quota=subprocess.run(['/usr/bin/lfs','quota','-q','-u',str(os.getuid()),str(campaign)],stdout=subprocess.PIPE,stderr=subprocess.PIPE,universal_newlines=True,timeout=10)
assert quota.returncode==0 and len(quota.stdout)<16384
numbers=quota.stdout.splitlines()[-1].split()[-8:]
used=int(numbers[4].rstrip('*'));limit=int(numbers[6])
parents={str(parent)for name in manifest['files']for parent in Path(name).parents if str(parent)!='.'}
required=1206+len(parents)+256
assert limit-used>=required,'Exact copy and result reserve exceed the remaining file quota'
directory.mkdir(exist_ok=False);source=directory/'source';source.mkdir()
total=0;old_total=0
for name in sorted(original['files']):
 pin=original['files'][name];assert 0<=pin['bytes']<=128*1024**2
 original_file=source_path(old/'source',name)
 raw=read_file(original_file,pin['bytes'])
 assert len(raw)==pin['bytes']and digest(raw)==pin['sha256']
 old_total+=len(raw);assert old_total<=original['expanded_bytes']
 replacement=payloads['provider.py']if name==provider else raw
 expected=manifest['files'][name]
 assert len(replacement)==expected['bytes']and digest(replacement)==expected['sha256']
 write_file(source/name,replacement);total+=len(replacement)
 assert total<=manifest['expanded_bytes']
assert total==manifest['expanded_bytes']and old_total==original['expanded_bytes']
observed=set()
for path in source.rglob('*'):
 assert not path.is_symlink()
 if path.is_file():
  name=path.relative_to(source).as_posix();assert name in manifest['files']
  pin=manifest['files'][name];raw=read_file(path,pin['bytes'])
  assert len(raw)==pin['bytes']and digest(raw)==pin['sha256'];observed.add(name)
assert observed==set(manifest['files'])
for name,pin in original['files'].items():
 raw=read_file(source_path(old/'source',name),pin['bytes'])
 assert len(raw)==pin['bytes']and digest(raw)==pin['sha256']
assert read_file(old/'manifest.json',1024*1024)==old_raw
for name in ('manifest.json','controller-source-pins.json'):write_file(directory/name,payloads[name])
for path in source.rglob('*'):
 if path.is_dir():path.chmod(0o555)
source.chmod(0o555)
record={'schema':'hydra-inference-source-copy-receipt-v1','completed':True,'directory':str(directory),'source':str(source),
 'derived_from_source':str(old/'source'),'manifest_sha256':pins['manifest.json'][1],
 'runtime_source_pins_file_sha256':pins['controller-source-pins.json'][1],
 'runtime_source_pins_sha256':digest(canonical(scope)), 'provider_sha256':pins['provider.py'][1],
 'verified_files':len(observed),'verified_bytes':total,'unchanged_files':1205,'uploaded_payload_bytes':sum(len(v)for v in payloads.values()),
 'wire_payload_bytes':len(request_raw),'archive_bytes_uploaded':0,'remote_archive_available':False,
 'local_reference_archive_sha256':manifest['archive_sha256'],'old_whitelisted_sources_unchanged':True,
 'non_whitelisted_files_copied':0,'saved_artifact_files_read':0,'hardlinks_created':0,
 'inference_only':True,'training_execution_allowed':False,'gpu_allocations':0,'model_calls':0,'native_runs':0,
 'automatic_retry':False,'elapsed_seconds':time.monotonic()-began,
 'inode_quota_before':{'used':used,'limit':limit,'required_with_reserve':required}}
write_file(directory/'transfer-receipt.json',json.dumps(record,sort_keys=True,indent=2).encode()+b'\n')
signal.alarm(0)
print(json.dumps(record),flush=True)
'''


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def prepared_request():
    ast.parse(REMOTE, feature_version=(3, 6))
    assert sha((HERE / "stage_p6_remote.py").read_bytes()) == "da136813840325da6c211169745a66c546dfc174a9d3a45d9475a7da96666f81"
    assert sha((HERE / "p6_smoke_transport.py").read_bytes()) == "6587fb953d693abfb76223c4a1fbd9dc8ace424f13e09017237a1a1240193d55"
    seal_raw = (BUNDLE / "local-seal.json").read_bytes()
    actual_raw = (BUNDLE / "actual-completion.json").read_bytes()
    assert sha(seal_raw) == SEAL_SHA and sha(actual_raw) == ACTUAL_SHA
    seal, actual = json.loads(seal_raw), json.loads(actual_raw)
    assert seal["status"] == "SEALED" and actual["completed"] is True and actual["actual_exit_code"] == 0
    assert actual["completion_chunk"] == "596530" and actual["training_execution_allowed"] is False
    paths = {"manifest.json": BUNDLE / "manifest.json",
             "controller-source-pins.json": BUNDLE / "controller-source-pins.json",
             "provider.py": BUNDLE / "source" / PROVIDER}
    raw_payloads = {name: path.read_bytes() for name, path in paths.items()}
    for name, raw in raw_payloads.items():
        assert {"bytes": len(raw), "sha256": sha(raw)} == PINS[name]
    return {"schema": "hydra-inference-source-copy-request-v1", "authority": "HYDRA_EXPERIMENT_AUTHORITY.md",
            "payloads": {name: base64.b64encode(raw).decode("ascii") for name, raw in raw_payloads.items()},
            "automatic_retry": False}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--stage", action="store_true", help="One explicit upload/copy; without this, validate locally only")
    args = parser.parse_args()
    request = prepared_request()
    payload = json.dumps(request, sort_keys=True, separators=(",", ":")).encode()
    assert len(payload) < 1024**2
    review = {"schema": "hydra-inference-source-copy-review-v1", "payload_pins": PINS,
              "raw_payload_bytes": sum(pin["bytes"] for pin in PINS.values()), "wire_payload_bytes": len(payload),
              "remote_script_sha256": sha(REMOTE.encode()), "source_files_copied": 1206,
              "changed_source_files": [PROVIDER], "archive_uploaded": False,
              "gpu_allocations": 0, "automatic_retry": False}
    if not args.stage:
        print(json.dumps(review), flush=True)
        return 0
    OUT.mkdir(exist_ok=False)
    (OUT / "review.json").write_text(json.dumps(review, indent=2) + "\n")
    (OUT / "remote-script.py").write_text(REMOTE)
    (OUT / "request.json").write_text(json.dumps({k: v for k, v in request.items() if k != "payloads"}, indent=2) + "\n")
    started = time.monotonic()
    result = run_ssh(SSH + ["python3 -c " + shlex.quote(REMOTE)], input=payload,
        stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=150, directory=OUT, phase="stage")
    (OUT / "stdout.json").write_bytes(result.stdout)
    (OUT / "stderr.txt").write_bytes(result.stderr)
    receipt = {"schema": "hydra-inference-source-stage-actual-completion-v1", "actual_ssh_exit_code": result.returncode,
               "elapsed_seconds": time.monotonic() - started, "review": review,
               "stdout_sha256": sha(result.stdout), "stderr_sha256": sha(result.stderr),
               "gpu_allocations": 0, "model_calls": 0, "native_runs": 0, "automatic_retry": False}
    (OUT / "actual-completion.json").write_text(json.dumps(receipt, indent=2) + "\n")
    print(result.stdout.decode(), end="")
    print(result.stderr.decode(), end="")
    print(json.dumps(receipt), flush=True)
    return result.returncode


if __name__ == "__main__":
    raise SystemExit(main())
