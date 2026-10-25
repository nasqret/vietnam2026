"""Upload the admitted 10.2 MB source/data package; no scheduler mutation."""
from pathlib import Path
import hashlib
import json
import shlex
import subprocess
import time

HERE = Path(__file__).resolve().parent
BUNDLE = HERE / "p6-source-bundle-04"
OUT = HERE / "p6-transfer-03"
REMOTE = "/net/scratch/hscra/plgrid/plgnasqret/codex-control/projects/peano-lab-training/experiments/hydra-practical-v1-20260904/bundles/source-data-04"
SSH = ["/usr/bin/ssh", "-T", "-o", "BatchMode=yes", "-o", "ConnectTimeout=15",
       "-o", "ServerAliveInterval=10", "-o", "ServerAliveCountMax=2", "-o", "ForwardAgent=no",
       "-o", "ClearAllForwardings=yes", "-o", "StrictHostKeyChecking=yes", "-o", "UpdateHostKeys=no",
       "-o", "ControlMaster=no", "-o", "ControlPath=none", "--", "plgnasqret@helios.cyfronet.pl"]
REMOTE_SCRIPT = r'''
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
assert str(directory)=='/net/scratch/hscra/plgrid/plgnasqret/codex-control/projects/peano-lab-training/experiments/hydra-practical-v1-20260904/bundles/source-data-04'
assert manifest['archive_bytes']==10256916 and manifest['archive_sha256']=='3afd1d93160c1695cc0f5bcc4030b77db2944e77178be532c02f26c564f03b73'
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
'''


def main():
    manifest = json.loads((BUNDLE / "manifest.json").read_bytes())
    admission = json.loads((BUNDLE / "admission.json").read_bytes())
    assert admission["completed"] and admission["actual_child_exit_code"] == 0 and admission["owned_child_reaped"]
    assert hashlib.sha256((BUNDLE / "manifest.json").read_bytes()).hexdigest() == "613a32e58b41e4ff1047b7da89b576fcc5c9afcb31137011de980f2f93e207f9"
    archive = (BUNDLE / "source-data.tar.gz").read_bytes()
    assert hashlib.sha256(archive).hexdigest() == manifest["archive_sha256"]
    OUT.mkdir(exist_ok=False)
    request = {"directory": REMOTE, "manifest": manifest}
    (OUT / "request.json").write_text(json.dumps(request, indent=2) + "\n")
    (OUT / "remote-script.py").write_text(REMOTE_SCRIPT)
    started = time.monotonic()
    result = subprocess.run(SSH + ["python3 -c " + shlex.quote(REMOTE_SCRIPT)],
        input=json.dumps(request).encode() + b"\n" + archive, stdout=subprocess.PIPE,
        stderr=subprocess.PIPE, timeout=200)
    (OUT / "stdout.txt").write_bytes(result.stdout)
    (OUT / "stderr.txt").write_bytes(result.stderr)
    receipt = {"actual_ssh_exit_code": result.returncode, "elapsed_seconds": time.monotonic()-started,
               "remote_directory": REMOTE, "archive_sha256": manifest["archive_sha256"],
               "gpu_allocations": 0, "automatic_retry": False}
    (OUT / "actual-completion.json").write_text(json.dumps(receipt, indent=2) + "\n")
    print(result.stdout.decode(), end="")
    print(result.stderr.decode(), end="")
    print(json.dumps(receipt), flush=True)
    return result.returncode


if __name__ == "__main__":
    raise SystemExit(main())
