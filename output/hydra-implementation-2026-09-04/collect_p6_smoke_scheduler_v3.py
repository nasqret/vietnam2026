"""One bounded read-only observation; no requeue, resubmit, resume or mutation."""
from pathlib import Path
import base64
import hashlib
import json
import shlex
import subprocess
import sys
import time

from stage_p6_remote import SSH
from p6_smoke_transport import run_ssh

HERE = Path(__file__).resolve().parent
ATTEMPT = HERE / "p6-smoke-4b-08"


def main():
    assert len(sys.argv)==2 and sys.argv[1].isdigit()
    output=ATTEMPT/("observation-"+sys.argv[1].zfill(2));output.mkdir(exist_ok=False)
    request=json.loads((ATTEMPT/"allocation-request.json").read_bytes())
    reservation=json.loads((ATTEMPT/"reservation.json").read_bytes())
    remote=r'''
import base64,hashlib,json,os,signal,subprocess,sys
from pathlib import Path
def phase_timeout(signum,frame):raise TimeoutError('Read-only collection exceeded 70 seconds; no automatic retry.')
signal.signal(signal.SIGALRM,phase_timeout);signal.alarm(70)
request=json.loads(sys.stdin.read(65536));directory=Path(request['directory']);job=request['job_id']
assert directory.name=='p6-smoke-4b-08'
bound=directory/'reservation.json';assert bound.is_file() and not bound.is_symlink() and bound.stat().st_size<=32768
reservation=json.loads(bound.read_bytes())
assert reservation==request['reservation'] and reservation['job_id']==job and reservation['uid']==os.getuid()
assert reservation['job_name']=='hydra-p6-smoke-4b-08' and reservation['seconds']==600
record={'job_id':job,'read_only':True,'files':{},'scheduler':{}};total=0
for name,args in (('sacct',['sacct','-n','-P','-j',job,'--format=JobIDRaw,State,ExitCode,ElapsedRaw,TimelimitRaw,AllocCPUS,ReqMem,AllocTRES%200,NodeList']),
                  ('scontrol',['scontrol','-o','show','job',job])):
 result=subprocess.run(args,stdout=subprocess.PIPE,stderr=subprocess.PIPE,universal_newlines=True,timeout=15)
 assert len(result.stdout.encode())+len(result.stderr.encode())<=65536
 record['scheduler'][name]={'actual_exit_code':result.returncode,'stdout':result.stdout,'stderr':result.stderr}
for relative in ('slurm.out','slurm.err','actual-process-exit.txt','reservation.json.claimed',
 'result/request.json','result/scheduler.jsonl','result/model-admission.json','result/primitive.json',
 'result/planner.json','result/throughput.json','result/completion.json'):
 path=directory/relative
 if not path.is_file():continue
 assert not path.is_symlink()
 size=path.stat().st_size
 assert size<=4*1024*1024 and total+size<=8*1024*1024
 with path.open('rb') as stream:raw=stream.read(size)
 assert len(raw)==size
 total+=len(raw)
 record['files'][relative]={'bytes':len(raw),'sha256':hashlib.sha256(raw).hexdigest(),
    'base64':base64.b64encode(raw).decode(),'unchanged_size_after_read':path.stat().st_size==size}
print(json.dumps(record),flush=True)
'''
    (output/"remote-script.py").write_text(remote)
    began=time.monotonic()
    result=run_ssh(SSH+["python3 -c "+shlex.quote(remote)],
        input=json.dumps({"directory":request["remote_job_directory"],"job_id":reservation["job_id"],"reservation":reservation}).encode(),
        stdout=subprocess.PIPE,stderr=subprocess.PIPE,timeout=90,directory=output,phase="collect")
    (output/"stderr.txt").write_bytes(result.stderr)
    (output/"transport-completion.json").write_text(json.dumps({"actual_ssh_exit_code":result.returncode,
        "elapsed_seconds":time.monotonic()-began,"read_only":True},indent=2)+"\n")
    if result.returncode:
        (output/"failed-stdout.txt").write_bytes(result.stdout)
        print(result.stderr.decode(),end="");return result.returncode
    value=json.loads(result.stdout)
    for relative,descriptor in value["files"].items():
        raw=base64.b64decode(descriptor.pop("base64"),validate=True)
        assert len(raw)==descriptor["bytes"] and hashlib.sha256(raw).hexdigest()==descriptor["sha256"]
        destination=output/relative;destination.parent.mkdir(parents=True,exist_ok=True);destination.write_bytes(raw)
    (output/"observation.json").write_text(json.dumps(value,indent=2)+"\n")
    summary={"scheduler":value["scheduler"]["sacct"],"files":list(value["files"])}
    completion=output/"result/completion.json"
    if completion.exists():
        report=json.loads(completion.read_bytes())
        summary["result"]={key:report.get(key) for key in ("completed","error","elapsed_seconds","sources_unchanged",
            "cold_load_seconds","decoders","throughput","peak_allocated_gpu_bytes")}
        summary["actual_model_activity"] = {key:report.get("session",{}).get(key) for key in ("actual_model_calls","forward_passes","generated_token_slots","last_generation_accounting")}
    throughput=output/"result/throughput.json"
    if throughput.exists():
        probe=json.loads(throughput.read_bytes())
        summary["probe"]={key:probe.get(key) for key in ("status","examples_completed","forward_calls","backward_calls","total_tokens","completion_tokens","elapsed_seconds","finite_gradients","optimizer_steps","trainable_tensors_unchanged")}
    print(json.dumps(summary),flush=True)
    return 0


if __name__=="__main__":raise SystemExit(main())
