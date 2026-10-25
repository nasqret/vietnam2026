"""Prepare, or explicitly stage, the sealed combined inference source 02.

Copy only the 1,325 pinned parent files on Helios and upload the ten reviewed
replacements, exact raw manifest and four source maps. No archive, saved model
output, application execution, scheduler mutation or automatic retry is allowed.
Default invocation is local metadata/hash validation only; --stage is the one
explicit remote mutation for the separately reviewed approval payload.
"""
from pathlib import Path
import argparse
import ast
import base64
import hashlib
import json
import os
import shlex
import stat
import subprocess
import time

from stage_p6_remote import SSH
from p6_smoke_transport import run_ssh

HERE = Path(__file__).resolve().parent
BUNDLE = HERE / "combined-source-bundle-02"
PARENT = HERE / "teacher-student-source-bundle-01"
OUT = HERE / "combined-inference-transfer-02"
CAMPAIGN = "/net/scratch/hscra/plgrid/plgnasqret/codex-control/projects/peano-lab-training/experiments/hydra-practical-v1-20260904"
OLD = CAMPAIGN + "/bundles/teacher-student-source-01"
DESTINATION = CAMPAIGN + "/bundles/combined-source-02"
MAX_REQUEST_BYTES = 2 * 1024**2
SEAL_SHA = "b8a2454e8c8f4e265442a7acdec2b09b9bce1d159fd58fe620d7a28a906dd8fd"
ACTUAL_SHA = "4ae069fe6a0ca0d2b8c84208bfa252e7f2b14003e040db8594338503f6e01b57"
GATE_SHA = "ca60f8c9e563da6f21328355e52dc06487abd3e027ba06fbccf1e52fd45ebad7"
CHANGES_SHA = "73fd2d08cc0c6f790c55250029664e20dfae09e5b1e5d275d4cf67e59d26e526"
PARENT_RAW_SHA = "69fd2873350245cfa9adf7095510fbfc6f993e165b35125eac18d7f737913e27"
PARENT_REMOTE_RAW_SHA = "0659d8ff51ec18aa617582473c705005a4e6166b700b31d20a6a4cdf19ca6307"
PARENT_CONTENT_SHA = "2ae6b0ed63d9c5b922f67e4e95f2050be28b37648fb21aa8a8673fdeb05be8a4"
METADATA_PINS = {
    "manifest.json": {"bytes": 256030, "sha256": "ae47bb1f0b6939c3f1ca8ac406024f832fc95b50ff505cf66648e94df0e578a7"},
    "paired-source-pins.json": {"bytes": 126170, "sha256": "f67019d3a6b693ef963a10d1e0d32b422d6bb0fb1e1fbee4614a6e10cf49d820"},
    "teacher-source-pins.json": {"bytes": 108200, "sha256": "e76da7607ea7be7681c30a5583bfb71c998aab7660754e28cb0c4cb61f5b3d7a"},
    "student-source-pins.json": {"bytes": 101298, "sha256": "8e55a8f20c5aaf8893d5850c008d0a54408cac9600d2827de4b6eeb95f2c887c"},
    "teacher-paired-source-pins.json": {"bytes": 126761, "sha256": "d184338a35b8aebde03a5edad16995038717502d4d84924da7f4750e36247ce9"},
}

# Python 3.6-compatible, standard-library-only file copier. The raw manifest pin
# determines the exact ten replacement paths and all source-map identities.
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
old=campaign/'bundles/teacher-student-source-01'
directory=campaign/'bundles/combined-source-02'
metadata_pins={
 'manifest.json':(256030,'ae47bb1f0b6939c3f1ca8ac406024f832fc95b50ff505cf66648e94df0e578a7'),
 'paired-source-pins.json':(126170,'f67019d3a6b693ef963a10d1e0d32b422d6bb0fb1e1fbee4614a6e10cf49d820'),
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
assert request['schema']=='hydra-combined-inference-source-copy-request-v2'
assert request['authority']=='HYDRA_EXPERIMENT_AUTHORITY.md' and request['automatic_retry']is False
assert isinstance(request['payloads'],dict) and len(request['payloads'])==15
payloads={name:base64.b64decode(value,validate=True)for name,value in request['payloads'].items()}
for name,(size,sha)in metadata_pins.items():assert len(payloads[name])==size and digest(payloads[name])==sha
manifest=json.loads(payloads['manifest.json'])
assert digest(canonical(manifest))=='4aeb37d8ad971975a22fe7cd879c69ad35e11246dccc5d37d7a9a0c2ab899ec1'
assert manifest['schema']=='hydra-combined-inference-source-v2' and manifest['runtime_destination']=='combined-source-02/source'
assert manifest['automatic_launch']is False and manifest['automatic_retry']is False
assert manifest['native_case_search_data_unchanged']is True and manifest['original_source_inputs_unchanged']is True
assert len(manifest['files'])==manifest['file_count']==1325 and manifest['expanded_bytes']==112065712
assert manifest['archive_sha256']=='5dd39a30a74eac192aac842c1eceabd1ee0fffdbf6cd9cd0e52ac658ea5def30'
assert manifest['provider_sha256']=='cc279710866146414c439e17935915f28d7dda7a44df20aa5d7e6bcd87994c44'
assert len(manifest['changed_files'])==manifest['changed_file_count']==10
changes=manifest['changed_files'];expected_payloads=set(metadata_pins)|{'source/'+name for name in changes}
assert set(payloads)==expected_payloads and sum(len(raw)for raw in payloads.values())==1059320
assert old.is_dir() and not old.is_symlink() and directory.parent.is_dir() and not directory.parent.is_symlink()
old_raw=read_file(old/'manifest.json',1024*1024);original=json.loads(old_raw)
assert digest(old_raw)=='0659d8ff51ec18aa617582473c705005a4e6166b700b31d20a6a4cdf19ca6307'
assert digest(canonical(original))=='2ae6b0ed63d9c5b922f67e4e95f2050be28b37648fb21aa8a8673fdeb05be8a4'
assert manifest['parent_manifest_sha256']=='69fd2873350245cfa9adf7095510fbfc6f993e165b35125eac18d7f737913e27'
assert original['archive_sha256']==manifest['parent_archive_sha256']=='a2196f8dfff25e940c72937feccfaaa562ddb5aac6952bd64fd117137f22fb3d'
assert len(original['files'])==original['file_count']==1325 and original['expanded_bytes']==112064116
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
scopes={}
for kind,pin in manifest['source_maps'].items():
 name=kind+'-source-pins.json';raw=payloads[name];scope=json.loads(raw)
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
for name in metadata_pins:write_file(directory/name,payloads[name])
for path in source.rglob('*'):
 if path.is_dir():path.chmod(0o555)
source.chmod(0o555)
record={'schema':'hydra-combined-inference-source-copy-receipt-v2','completed':True,'directory':str(directory),'source':str(source),
 'derived_from_source':str(old/'source'),'manifest_sha256':metadata_pins['manifest.json'][1],
 'manifest_content_sha256':digest(canonical(manifest)),'manifest_raw_bytes_preserved':True,
 'parent_remote_manifest_sha256':digest(old_raw),'parent_manifest_content_sha256':digest(canonical(original)),
 'parent_local_manifest_sha256':manifest['parent_manifest_sha256'],'source_maps':scopes,
 'provider_sha256':manifest['provider_sha256'],'provider_profile':manifest['provider_profile'],
 'verified_files':len(observed),'verified_bytes':total,'unchanged_files':1315,'changed_files':sorted(changes),
 'uploaded_payload_files':len(payloads),'uploaded_payload_bytes':sum(len(v)for v in payloads.values()),
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
'''


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False).encode()


def stamp(value):
    return (value.st_dev, value.st_ino, value.st_mode, value.st_nlink,
            value.st_size, value.st_mtime_ns, value.st_ctime_ns)


def read_local(path, maximum=1024**2):
    assert path.is_file() and not path.is_symlink()
    before = path.lstat()
    assert stat.S_ISREG(before.st_mode) and before.st_size <= maximum
    with path.open("rb") as stream:
        assert stamp(os.fstat(stream.fileno())) == stamp(before)
        raw = stream.read(maximum + 1)
        assert stamp(os.fstat(stream.fileno())) == stamp(before)
    assert len(raw) == before.st_size and stamp(path.lstat()) == stamp(before)
    return raw


def prepared_request():
    ast.parse(REMOTE, feature_version=(3, 6))
    assert sha(read_local(HERE / "stage_p6_remote.py")) == "da136813840325da6c211169745a66c546dfc174a9d3a45d9475a7da96666f81"
    assert sha(read_local(HERE / "p6_smoke_transport.py")) == "6587fb953d693abfb76223c4a1fbd9dc8ace424f13e09017237a1a1240193d55"
    seal_raw = read_local(BUNDLE / "SEALED.json")
    actual_raw = read_local(BUNDLE / "actual-completion.json")
    gate_raw = read_local(BUNDLE / "gate-completion.json")
    assert sha(seal_raw) == SEAL_SHA and sha(actual_raw) == ACTUAL_SHA and sha(gate_raw) == GATE_SHA
    seal, actual, gate = (json.loads(raw) for raw in (seal_raw, actual_raw, gate_raw))
    assert seal["status"] == "SEALED_FILE_ONLY_GATE_PASSED" and seal["source_file_count"] == 1325
    assert actual["actual_exit_code"] == 0 and actual["actual_completion_chunk"] == "698c04"
    assert gate["passed"] is True and gate["source_inputs_unchanged"] is True
    assert all(actual[key] == 0 for key in ("native_runs", "model_calls", "scheduler_queries", "allocations", "uploads"))
    payloads = {name: read_local(BUNDLE / name) for name in METADATA_PINS}
    for name, raw in payloads.items():
        assert {"bytes": len(raw), "sha256": sha(raw)} == METADATA_PINS[name] == seal["files"][name]
    manifest = json.loads(payloads["manifest.json"])
    assert sha(canonical(manifest)) == "4aeb37d8ad971975a22fe7cd879c69ad35e11246dccc5d37d7a9a0c2ab899ec1"
    parent_raw = read_local(PARENT / "manifest.json")
    assert sha(parent_raw) == PARENT_RAW_SHA
    parent = json.loads(parent_raw)
    assert sha(canonical(parent)) == PARENT_CONTENT_SHA
    changes_raw = read_local(BUNDLE / "changed-files.json")
    assert sha(changes_raw) == CHANGES_SHA
    changes = json.loads(changes_raw)
    assert changes == manifest["changed_files"] and len(changes) == 10
    assert len(parent["files"]) == len(manifest["files"]) == 1325
    assert set(parent["files"]) == set(manifest["files"])
    assert {name for name in manifest["files"] if manifest["files"][name] != parent["files"][name]} == set(changes)
    for name, change in changes.items():
        assert change["before"] == parent["files"][name] and change["after"] == manifest["files"][name]
        raw = read_local(BUNDLE / "source" / name)
        assert {"bytes": len(raw), "sha256": sha(raw)} == change["after"]
        payloads["source/" + name] = raw
    for kind, pin in manifest["source_maps"].items():
        raw = payloads[kind + "-source-pins.json"]
        scope = json.loads(raw)
        assert len(scope) == pin["files"] and sha(canonical(scope)) == pin["content_sha256"]
        if kind == "teacher":
            assert all(manifest["files"][name]["sha256"] == value for name, value in scope.items())
        else:
            assert all(manifest["files"][name] == value for name, value in scope.items())
    assert len(payloads) == 15 and sum(map(len, payloads.values())) == 1059320
    return {"schema": "hydra-combined-inference-source-copy-request-v2", "authority": "HYDRA_EXPERIMENT_AUTHORITY.md",
            "payloads": {name: base64.b64encode(raw).decode("ascii") for name, raw in payloads.items()},
            "automatic_retry": False}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--stage", action="store_true", help="One explicit approved upload/copy; default is local validation only")
    args = parser.parse_args()
    request = prepared_request()
    payload = canonical(request)
    assert len(payload) <= MAX_REQUEST_BYTES
    payload_pins = {name: {"bytes": len(raw), "sha256": sha(raw)}
                    for name, value in request["payloads"].items()
                    for raw in (base64.b64decode(value, validate=True),)}
    review = {"schema": "hydra-combined-inference-source-copy-review-v2", "payload_pins": payload_pins,
              "raw_payload_bytes": sum(pin["bytes"] for pin in payload_pins.values()),
              "wire_payload_bytes": len(payload), "wire_payload_sha256": sha(payload),
              "remote_script_sha256": sha(REMOTE.encode()), "remote_script_bytes": len(REMOTE.encode()),
              "source_files_copied": 1325, "unchanged_source_files": 1315,
              "changed_source_files": sorted(name[len("source/"):] for name in payload_pins if name.startswith("source/")),
              "remote_parent": OLD, "remote_destination": DESTINATION,
              "parent_local_manifest_sha256": PARENT_RAW_SHA,
              "parent_remote_manifest_sha256": PARENT_REMOTE_RAW_SHA,
              "parent_manifest_content_sha256": PARENT_CONTENT_SHA,
              "manifest_raw_bytes_preserved": True, "archive_uploaded": False,
              "bounds": {"wire_bytes": MAX_REQUEST_BYTES, "expanded_bytes": 112065712,
                         "remote_cpu_soft_seconds": 60, "remote_cpu_hard_seconds": 75,
                         "remote_wall_seconds": 120, "remote_address_space_bytes": 512 * 1024**2,
                         "ssh_wall_seconds": 150, "quota_query_wall_seconds": 10},
              "application_executions": 0, "gpu_allocations": 0, "automatic_retry": False}
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
    receipt = {"schema": "hydra-combined-inference-source-stage-actual-completion-v2",
               "actual_ssh_exit_code": result.returncode, "elapsed_seconds": time.monotonic() - started,
               "review": review, "stdout_sha256": sha(result.stdout), "stderr_sha256": sha(result.stderr),
               "gpu_allocations": 0, "model_calls": 0, "native_runs": 0, "automatic_retry": False}
    (OUT / "actual-completion.json").write_text(json.dumps(receipt, indent=2) + "\n")
    print(result.stdout.decode(errors="replace"), end="")
    print(result.stderr.decode(errors="replace"), end="")
    print(json.dumps(receipt), flush=True)
    return result.returncode


if __name__ == "__main__":
    raise SystemExit(main())
