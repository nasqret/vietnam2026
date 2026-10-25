"""Upload one separately sealed decoder-v2 bundle; never allocate or launch."""
from pathlib import Path
import hashlib
import json
import shlex
import subprocess
import time

from stage_p6_remote import SSH

HERE = Path(__file__).resolve().parent
BUNDLE = HERE / "p6-source-bundle-05"
OUT = HERE / "p6-transfer-05"
CAMPAIGN = "/net/scratch/hscra/plgrid/plgnasqret/codex-control/projects/peano-lab-training/experiments/hydra-practical-v1-20260904"
PROVIDER_SHA = "7bacd4f97272093873db76ea7b2178e1074ca3ff5f2ef88b4e411933c131580f"
CHANGED = {"hydra-playground/experimental_model.py",
           "output/p6-prototype/remote_provider_smoke.py",
           "output/p6-prototype/remote_training_pilot.py"}
REMOTE = r'''
import hashlib,json,os,signal,subprocess,sys,tarfile,time
from pathlib import Path
os.umask(0o077);signal.alarm(150);began=time.monotonic()
header=sys.stdin.buffer.readline(1024*1024+1)
assert len(header)<=1024*1024 and header.endswith(b'\n')
request=json.loads(header);manifest=request['manifest']
directory=Path(request['directory'])
assert str(directory)=='/net/scratch/hscra/plgrid/plgnasqret/codex-control/projects/peano-lab-training/experiments/hydra-practical-v1-20260904/bundles/source-data-06'
assert manifest['file_count']==1206 and 0<manifest['expanded_bytes']<128*1024*1024
assert 0<manifest['archive_bytes']<16*1024*1024 and not directory.exists()
assert manifest['files']['hydra-playground/experimental_model.py']['sha256']=='7bacd4f97272093873db76ea7b2178e1074ca3ff5f2ef88b4e411933c131580f'
quota=subprocess.run(['/usr/bin/lfs','quota','-q','-u',str(os.getuid()),str(directory.parent.parent)],stdout=subprocess.PIPE,stderr=subprocess.PIPE,universal_newlines=True,timeout=10)
assert quota.returncode==0 and len(quota.stdout)<16384
numbers=quota.stdout.splitlines()[-1].split()[-8:]
used=int(numbers[4].rstrip('*'));limit=int(numbers[6])
parents={str(parent)for name in manifest['files'] for parent in Path(name).parents if str(parent)!='.'}
required=manifest['file_count']+len(parents)+256
assert limit-used>=required,'Exact new extraction and result reserve exceed remaining file quota'
directory.mkdir(exist_ok=False);archive=directory/'source-data.tar.gz'
remaining=manifest['archive_bytes'];digest=hashlib.sha256()
with archive.open('xb')as stream:
 while remaining:
  block=sys.stdin.buffer.read(min(1024*1024,remaining));assert block,'Premature upload EOF'
  stream.write(block);digest.update(block);remaining-=len(block)
 assert not sys.stdin.buffer.read(1),'Unexpected trailing upload bytes'
assert digest.hexdigest()==manifest['archive_sha256']
source=directory/'source';source.mkdir();observed=set();total=0
with tarfile.open(str(archive),'r:gz')as tar:
 for item in tar:
  assert item.name not in observed and item.name in manifest['files']
  observed.add(item.name);pin=manifest['files'][item.name];path=Path(item.name)
  assert item.isfile() and not path.is_absolute() and '..'not in path.parts and item.size==pin['bytes']
  raw=tar.extractfile(item).read(item.size+1)
  assert len(raw)==pin['bytes'] and hashlib.sha256(raw).hexdigest()==pin['sha256']
  total+=len(raw);assert total<=manifest['expanded_bytes']
  target=source/path;target.parent.mkdir(parents=True,exist_ok=True)
  with target.open('xb')as stream:stream.write(raw)
  target.chmod(0o444)
assert observed==set(manifest['files']) and total==manifest['expanded_bytes']
(directory/'manifest.json').write_text(json.dumps(manifest,indent=2,sort_keys=True)+'\n')
record={'schema':'hydra-source-transfer-receipt-v1','directory':str(directory),'source':str(source),
 'archive_sha256':digest.hexdigest(),'verified_files':len(observed),'verified_bytes':total,
 'elapsed_seconds':time.monotonic()-began,'gpu_allocations':0,'automatic_retry':False,
 'inode_quota_before':{'used':used,'limit':limit,'required_with_reserve':required},
 'old_source_and_results_unchanged':True,'decoder_revision':'beam-callback-accounting-v2'}
(directory/'transfer-receipt.json').write_text(json.dumps(record,indent=2)+'\n')
print(json.dumps(record),flush=True)
'''


def main():
    old = json.loads((HERE / "p6-source-bundle-04/manifest.json").read_bytes())
    manifest_raw = (BUNDLE / "manifest.json").read_bytes()
    manifest = json.loads(manifest_raw)
    assert manifest["file_count"] == len(manifest["files"]) == 1206
    assert set(manifest["files"]) == set(old["files"])
    assert {name for name in old["files"] if old["files"][name] != manifest["files"][name]} == CHANGED
    assert manifest["files"]["hydra-playground/experimental_model.py"]["sha256"] == PROVIDER_SHA
    archive = (BUNDLE / "source-data.tar.gz").read_bytes()
    assert len(archive) == manifest["archive_bytes"]
    assert hashlib.sha256(archive).hexdigest() == manifest["archive_sha256"]
    OUT.mkdir(exist_ok=False)
    request = {"authority": "HYDRA_EXPERIMENT_AUTHORITY.md", "directory": CAMPAIGN + "/bundles/source-data-06",
               "manifest": manifest, "local_manifest_sha256": hashlib.sha256(manifest_raw).hexdigest(),
               "change": "Only the reviewed decoder callback fix and its two dependent controller pins; original inputs, configs and data remain identical."}
    (OUT / "request.json").write_text(json.dumps(request, indent=2) + "\n")
    (OUT / "remote-script.py").write_text(REMOTE)
    began = time.monotonic()
    result = subprocess.run(SSH + ["python3 -c " + shlex.quote(REMOTE)],
        input=json.dumps(request).encode() + b"\n" + archive,
        stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=170)
    (OUT / "stdout.json").write_bytes(result.stdout)
    (OUT / "stderr.txt").write_bytes(result.stderr)
    receipt = {"actual_ssh_exit_code": result.returncode, "elapsed_seconds": time.monotonic()-began,
               "archive_sha256": manifest["archive_sha256"], "archive_bytes": len(archive),
               "remote_directory": request["directory"], "gpu_allocations": 0, "automatic_retry": False}
    (OUT / "actual-completion.json").write_text(json.dumps(receipt, indent=2) + "\n")
    print(result.stdout.decode(), end="")
    print(result.stderr.decode(), end="")
    print(json.dumps(receipt), flush=True)
    return result.returncode


if __name__ == "__main__":
    raise SystemExit(main())
