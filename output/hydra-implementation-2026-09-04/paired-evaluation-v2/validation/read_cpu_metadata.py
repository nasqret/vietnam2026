"""One authorized, read-only Helios CPU association/partition query; never submit."""
from hashlib import sha256
import importlib.util
import json
from pathlib import Path
import shlex
import subprocess
import time

HERE = Path(__file__).resolve().parent
STAGE = HERE.parents[1] / "stage_p6_remote.py"
OUT = HERE / "cpu-association-01"
REMOTE = r'''
import json,os,pwd,signal,subprocess,time
signal.alarm(30)
assert os.getuid()==105923, "Unexpected remote owner"
user=pwd.getpwuid(os.getuid()).pw_name
assert user=="plgnasqret", "Unexpected remote user"
commands=[
 ["sacctmgr","-n","-P","show","associations","where","user="+user,
  "format=Cluster,Account%80,User%40,Partition%40,QOS%120,DefaultQOS%80"],
 ["sinfo","--noheader","--format=%P|%a|%l|%G|%D|%c|%m"],
 ["scontrol","-o","show","partition","plgrid"],
]
rows=[]
started=time.monotonic()
for command in commands:
 try:
  process=subprocess.run(command,stdout=subprocess.PIPE,stderr=subprocess.PIPE,universal_newlines=True,timeout=8)
  assert len(process.stdout.encode())<=65536 and len(process.stderr.encode())<=8192,"Metadata output bound exceeded"
  rows.append({"argv":command,"exit_code":process.returncode,"stdout":process.stdout,"stderr":process.stderr})
 except Exception as error:
  rows.append({"argv":command,"exit_code":None,"error":type(error).__name__+": "+str(error)[:500]})
print(json.dumps({"schema":"hydra-owned-cpu-metadata-v1","uid":os.getuid(),"user":user,"commands":rows,
 "elapsed_seconds":time.monotonic()-started,"scheduler_mutations":0,"uploads":0,"native_runs":0,"model_calls":0,"gpu_allocations":0,"automatic_retry":False}),flush=True)
'''


def main():
    spec = importlib.util.spec_from_file_location("hydra_readonly_existing_stage", STAGE)
    stage = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(stage)
    assert stage.SSH[-1] == "plgnasqret@helios.cyfronet.pl"
    OUT.mkdir(exist_ok=False)
    request = {"schema": "hydra-readonly-cpu-query-request-v1", "ssh": stage.SSH,
        "remote_script_sha256": sha256(REMOTE.encode()).hexdigest(),
        "stage_source_sha256": sha256(STAGE.read_bytes()).hexdigest(), "remote_uid": 105923,
        "maximum_ssh_calls": 1, "read_only": True, "automatic_retry": False}
    (OUT / "request.json").write_text(json.dumps(request, indent=2) + "\n")
    (OUT / "remote-script.py").write_text(REMOTE)
    began = time.monotonic()
    process = subprocess.run(stage.SSH + ["python3 -c " + shlex.quote(REMOTE)],
        stdin=subprocess.DEVNULL, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=45)
    (OUT / "stdout.json").write_bytes(process.stdout)
    (OUT / "stderr.txt").write_bytes(process.stderr)
    result = {"actual_ssh_exit_code": process.returncode, "elapsed_seconds": time.monotonic() - began,
        "actual_ssh_calls": 1, "scheduler_mutations": 0, "uploads": 0,
        "native_runs": 0, "model_calls": 0, "gpu_allocations": 0, "automatic_retry": False}
    (OUT / "ssh-completion.json").write_text(json.dumps(result, indent=2) + "\n")
    print(process.stdout.decode(), end="")
    print(process.stderr.decode(), end="")
    print(json.dumps(result), flush=True)
    return process.returncode


if __name__ == "__main__":
    raise SystemExit(main())
