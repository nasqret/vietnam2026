"""Bind and release the already-held smoke once, under the campaign ceiling."""
from pathlib import Path
import hashlib
import json
import re
import shlex
import subprocess
import time

from stage_p6_remote import SSH
from p6_smoke_transport import run_ssh

HERE = Path(__file__).resolve().parent
OUT = HERE / "p6-smoke-4b-08"


def main():
    submission = json.loads((OUT / "submit.stdout").read_bytes())
    spec = json.loads((OUT / "allocation-request.json").read_bytes())
    assert submission["actual_sbatch_exit_code"] == 0 and submission["held"] and not submission["released"]
    job = submission["stdout"].strip()
    assert re.fullmatch(r"[0-9]{1,20}", job)
    reservation = {"schema":"hydra-p6-smoke-reservation-v1", "job_id":job,
        "job_name":spec["job_name"], "nonce":spec["nonce"], "uid":submission["uid"],
        **{key:spec[key] for key in ("account","partition","model_key","gpus","nodes","cpus","memory_gib","seconds")}}
    raw = json.dumps(reservation,sort_keys=True,separators=(",", ":"),allow_nan=False).encode()+b"\n"
    identity = hashlib.sha256(raw).hexdigest()
    with (OUT / "reservation.json").open("xb") as stream: stream.write(raw)
    campaign = json.loads((HERE / "campaign.json").read_bytes())
    assert campaign["gpu_hours_allocated"]*3600 + 600 <= campaign["campaign_gpu_hours_ceiling"]*3600
    campaign["gpu_hours_allocated"] += 600/3600
    for row in campaign["gpu_reservations"]:
        if row["attempt"] == "p6-smoke-4b-08":
            row.update(status="release_requested",job_id=job,reservation_sha256=identity,allocated_seconds=600)
    campaign["gpu_seconds_reserved"] = max(campaign["gpu_seconds_reserved"],
        sum(row.get("allocated_seconds", 0) for row in campaign["gpu_reservations"]))
    assert campaign["gpu_seconds_reserved"] <= campaign["campaign_gpu_hours_ceiling"] * 3600
    (HERE / "campaign.json").write_text(json.dumps(campaign,indent=2)+"\n")
    remote = r'''
import hashlib,json,os,re,signal,subprocess,sys
from pathlib import Path
def phase_timeout(signum,frame):raise TimeoutError('Release phase exceeded 70 seconds; retain full charge and do not retry.')
signal.signal(signal.SIGALRM,phase_timeout);signal.alarm(70)
request=json.loads(sys.stdin.read(128*1024))
record=request['reservation'];job=record['job_id'];directory=Path(request['directory'])
raw=request['raw'].encode();assert hashlib.sha256(raw).hexdigest()==request['sha256']
assert json.loads(raw)==record and record['uid']==os.getuid()
assert directory.is_dir() and directory.name=='p6-smoke-4b-08'
query=subprocess.run(['scontrol','-o','show','job',job],stdout=subprocess.PIPE,stderr=subprocess.PIPE,universal_newlines=True,timeout=15)
assert query.returncode==0 and len(query.stdout.encode())<=65536
fields=dict(re.findall(r'(?:^|\s)([A-Za-z][A-Za-z0-9]*)=([^\s]+)',query.stdout))
assert fields.get('JobId')==job and fields.get('JobName')==record['job_name']
assert fields.get('Comment')=='hydra-p6:'+record['nonce'] and fields.get('JobState')=='PENDING'
assert fields.get('Reason')=='JobHeldUser' and fields.get('Requeue')=='0' and fields.get('Restarts')=='0'
assert fields.get('Account')==record['account'] and fields.get('Partition')==record['partition']
assert fields.get('TimeLimit')=='00:10:00' and fields.get('NumCPUs')=='8'
assert re.fullmatch(r'[^()]+\('+str(os.getuid())+r'\)',fields.get('UserId',''))
tres=dict(item.split('=',1) for item in fields['ReqTRES'].split(','))
assert tres.get('cpu')=='8' and tres.get('mem')=='64G' and tres.get('node')=='1' and tres.get('gres/gpu')=='1'
queue=subprocess.run(['squeue','--array','-h','-u',str(os.getuid()),'-o','%i|%b'],stdout=subprocess.PIPE,stderr=subprocess.PIPE,universal_newlines=True,timeout=15)
assert queue.returncode==0 and len(queue.stdout.encode())<=16384
for line in queue.stdout.splitlines():
 identifier,gres=line.split('|',1)
 assert identifier==job or gres in ('N/A','(null)',''),'Another owned GPU job appeared; do not release'
with (directory/'reservation.json').open('xb') as stream:stream.write(raw)
with (directory/'reservation.sha256').open('x') as stream:stream.write(request['sha256']+'\n')
with (directory/'release-request.json').open('x') as stream:json.dump({'job_id':job,'reservation_sha256':request['sha256'],'before':fields,'automatic_retry':False},stream)
result=subprocess.run(['scontrol','release',job],stdout=subprocess.PIPE,stderr=subprocess.PIPE,universal_newlines=True,timeout=15)
receipt={'actual_release_exit_code':result.returncode,'stdout':result.stdout,'stderr':result.stderr,
 'job_id':job,'reservation_sha256':request['sha256'],'released':result.returncode==0,'allocated_seconds_ceiling':600,'automatic_retry':False}
with (directory/'release-completion.json').open('x') as stream:json.dump(receipt,stream,indent=2)
print(json.dumps(receipt),flush=True)
sys.exit(result.returncode)
'''
    (OUT / "release-remote-script.py").write_text(remote)
    payload = {"reservation":reservation,"raw":raw.decode(),"sha256":identity,"directory":spec["remote_job_directory"]}
    started=time.monotonic()
    result=run_ssh(SSH+["python3 -c "+shlex.quote(remote)],input=json.dumps(payload).encode(),
        stdout=subprocess.PIPE,stderr=subprocess.PIPE,timeout=90,directory=OUT,phase="release")
    (OUT/"release.stdout").write_bytes(result.stdout)
    (OUT/"release.stderr").write_bytes(result.stderr)
    (OUT/"release-completion.json").write_text(json.dumps({"actual_ssh_exit_code":result.returncode,
        "elapsed_seconds":time.monotonic()-started,"allocated_seconds_ceiling":600,"job_id":job,
        "reservation_sha256":identity,"automatic_retry":False},indent=2)+"\n")
    print(result.stdout.decode(),end="");print(result.stderr.decode(),end="")
    return result.returncode


if __name__=="__main__":
    raise SystemExit(main())
