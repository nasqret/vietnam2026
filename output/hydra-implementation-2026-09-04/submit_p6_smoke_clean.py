"""Prepare exactly one held 600-second GH200 smoke; never release or retry it."""
from pathlib import Path
import hashlib
import json
import secrets
import shlex
import subprocess
import time

from stage_p6_remote import SSH

HERE = Path(__file__).resolve().parent
OUT = HERE / "p6-smoke-4b-05"
PROJECT = "/net/scratch/hscra/plgrid/plgnasqret/codex-control/projects/peano-lab-training"
CAMPAIGN = PROJECT + "/experiments/hydra-practical-v1-20260904"
SOURCE = CAMPAIGN + "/bundles/source-data-03/source"
JOB = CAMPAIGN + "/jobs/p6-smoke-4b-05"
NAME = "hydra-p6-smoke-4b-05"


def main():
    transfer = json.loads((HERE / "p6-transfer-02/actual-completion.json").read_bytes())
    assert transfer["actual_ssh_exit_code"] == 0
    admission = json.loads((HERE / "p6-linux-data-admission-v2-01/stdout.json").read_bytes())
    assert admission["completed"] and admission["exact_plan_match"]
    assert admission["plan_sha256"] == "0d4a80e91aba0dedfb3b8f4434540ab687e7361375268c4ebfd62e815719dd4e"
    base_admission = json.loads((HERE / "p6-clean-base-admission-01/stdout.jsonl").read_bytes().splitlines()[-1])
    assert base_admission["completed"]
    assert base_admission["models"]["qwen3-4b-base"]["identity"]["base_identity_sha256"] == "16d5299fe64198d6b9f4bb6dc6c1e7ef21ca3c232193d6549857200e6391def0"
    OUT.mkdir(exist_ok=False)
    nonce = secrets.token_hex(16)
    command = [PROJECT + "/.venv-helios/bin/python", "-B", "-P",
        SOURCE + "/output/p6-prototype/remote_provider_smoke.py", "--app-root", SOURCE + "/hydra-playground",
        "--reservation", JOB + "/reservation.json", "--reservation-sha256", "RESERVATION_SHA_PLACEHOLDER",
        "--base-directory", CAMPAIGN + "/authenticated-bases-01/qwen3-4b-base", "--output", JOB + "/result",
        "--throughput-examples", "8", "--throughput-config",
        SOURCE + "/hydra-playground/training-v5/configs/qwen3_4b_decisions_v2_pilot.toml",
        "--dataset-manifest", "output/hydra-implementation-2026-09-04/decisions-v2-01/manifest.json",
        "--dataset-sha256", "e575970df58d046735f492acaf22e1cdea44445608a201c62d0644590b95ea77"]
    invocation = " ".join(shlex.quote(x) for x in command).replace("RESERVATION_SHA_PLACEHOLDER", '"$HYDRA_RESERVATION_SHA"')
    script = "\n".join(["#!/bin/bash -l", "set -euo pipefail", "umask 077", "module purge",
        "module load ML-bundle/25.10", "unset PYTHONPATH", "export PYTHONHASHSEED=20260904",
        "export PYTHONDONTWRITEBYTECODE=1 PYTHONNOUSERSITE=1", "export HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1",
        "export TOKENIZERS_PARALLELISM=false OMP_NUM_THREADS=1", "cd " + shlex.quote(SOURCE),
        "read -r HYDRA_RESERVATION_SHA < " + shlex.quote(JOB + "/reservation.sha256"), "set +e", invocation,
        "HYDRA_ACTUAL_EXIT=$?", "printf '%s\\n' \"$HYDRA_ACTUAL_EXIT\" > " + shlex.quote(JOB + "/actual-process-exit.txt"),
        'exit "$HYDRA_ACTUAL_EXIT"', ""])
    spec = {"schema":"hydra-p6-smoke-allocation-v1", "authority":"HYDRA_EXPERIMENT_AUTHORITY.md",
        "job_name":NAME, "nonce":nonce, "account":"plgccaiautore2026-gpu-gh200",
        "partition":"plgrid-gpu-gh200", "model_key":"qwen3-4b-base", "gpus":1, "nodes":1,
        "cpus":8, "memory_gib":64, "seconds":600, "remote_job_directory":JOB,
        "source_archive_sha256":transfer["archive_sha256"], "script_sha256":hashlib.sha256(script.encode()).hexdigest(),
        "optimizer_updates":0, "maximum_actual_model_calls":2, "maximum_gradient_examples":8,
        "submit_held":True, "requeue":False, "automatic_retry":False,
        "submission_preflight_fix":"Attempt03 stopped before sbatch on compressed unrelated CPU job array IDs. Enumerate array elements and verify each exact ArrayJobId/ArrayTaskId and GPU TRES; leave all other jobs untouched.",
        "diagnosed_followup":"21908771 failed before model load because download-receipt.json was beside pinned model files. A new clean view preserves downloads/receipts and now passes full unchanged authenticate_base CPU hashing. Same source, theorem, two calls and eight no-update gradient examples; no sweep or automatic retry. Earlier dataset portability issue also passed exact Linux CPU admission."}
    (OUT / "allocation-request.json").write_text(json.dumps(spec, indent=2)+"\n")
    (OUT / "job.sbatch").write_text(script)
    campaign = json.loads((HERE / "campaign.json").read_bytes())
    reserved = campaign.get("gpu_seconds_reserved", round(campaign.get("gpu_hours_allocated",0)*3600))
    assert reserved + 600 <= campaign["campaign_gpu_hours_ceiling"] * 3600
    campaign["gpu_seconds_reserved"] = reserved + 600
    campaign.setdefault("gpu_reservations", []).append({"attempt":"p6-smoke-4b-05", "seconds":600,
        "gpus":1, "status":"prepared_for_held_submission", "request":"p6-smoke-4b-05/allocation-request.json"})
    (HERE / "campaign.json").write_text(json.dumps(campaign, indent=2)+"\n")
    remote = r'''
import hashlib,json,os,re,subprocess,sys
from pathlib import Path
os.umask(0o077)
request=json.loads(sys.stdin.read(128*1024))
spec=request['spec'];script=request['script']
assert hashlib.sha256(script.encode()).hexdigest()==spec['script_sha256']
directory=Path(spec['remote_job_directory'])
assert str(directory).endswith('/hydra-practical-v1-20260904/jobs/p6-smoke-4b-05')
queue=subprocess.run(['squeue','--array','-h','-u',str(os.getuid()),'-o','%i|%T|%j|%b'],stdout=subprocess.PIPE,stderr=subprocess.PIPE,universal_newlines=True,timeout=10)
assert queue.returncode==0 and len(queue.stdout.encode())<=16384
rows=queue.stdout.strip().splitlines();assert len(rows)<=32
observed=[]
for row in rows:
 job=row.split('|')[0].strip();assert re.fullmatch(r'[0-9]{1,20}(?:_[0-9]{1,10})?',job)
 query=subprocess.run(['scontrol','-o','show','job',job],stdout=subprocess.PIPE,stderr=subprocess.PIPE,universal_newlines=True,timeout=5)
 assert query.returncode==0 and len(query.stdout.encode())<=65536
 fields=dict(re.findall(r'(?:^|\s)([A-Za-z][A-Za-z0-9]*)=([^\s]+)',query.stdout))
 assert 'ReqTRES' in fields
 if '_' in job:
  base,task=job.split('_');assert fields.get('ArrayJobId')==base and fields.get('ArrayTaskId')==task
 else:assert fields.get('JobId')==job
 assert 'gres/gpu' not in fields['ReqTRES'] and 'gres/gpu' not in fields.get('AllocTRES',''),'Another owned GPU allocation/reservation exists'
 observed.append({'job_id':job,'requested_tres':fields['ReqTRES'],'allocated_tres':fields.get('AllocTRES'), 'left_unchanged':True})
directory.mkdir(parents=True,exist_ok=False)
(directory/'job.sbatch').write_text(script)
(directory/'allocation-request.json').write_text(json.dumps(spec,indent=2)+'\n')
command=['sbatch','--hold','--parsable','--no-requeue','--account='+spec['account'],'--partition='+spec['partition'],
 '--nodes=1','--ntasks=1','--cpus-per-task=8','--mem=64G','--gres=gpu:1','--time=00:10:00',
 '--job-name='+spec['job_name'],'--comment=hydra-p6:'+spec['nonce'],
 '--chdir='+str(directory),'--output='+str(directory/'slurm.out'),'--error='+str(directory/'slurm.err'),str(directory/'job.sbatch')]
result=subprocess.run(command,stdout=subprocess.PIPE,stderr=subprocess.PIPE,universal_newlines=True,timeout=20)
record={'actual_sbatch_exit_code':result.returncode,'stdout':result.stdout,'stderr':result.stderr,
 'uid':os.getuid(),'command':command,'held':True,'released':False,'gpu_seconds':0,'automatic_retry':False,'other_cpu_jobs':observed}
(directory/'held-submission.json').write_text(json.dumps(record,indent=2)+'\n')
print(json.dumps(record),flush=True)
sys.exit(result.returncode)
'''
    (OUT / "submit-remote-script.py").write_text(remote)
    started = time.monotonic()
    result = subprocess.run(SSH + ["python3 -c " + shlex.quote(remote)],
        input=json.dumps({"spec":spec,"script":script}).encode(),stdout=subprocess.PIPE,stderr=subprocess.PIPE,timeout=60)
    (OUT / "submit.stdout").write_bytes(result.stdout)
    (OUT / "submit.stderr").write_bytes(result.stderr)
    receipt = {"actual_ssh_exit_code":result.returncode, "elapsed_seconds":time.monotonic()-started,
               "release_attempted":False, "automatic_retry":False}
    (OUT / "submit-completion.json").write_text(json.dumps(receipt, indent=2)+"\n")
    print(result.stdout.decode(),end=""); print(result.stderr.decode(),end=""); print(json.dumps(receipt))
    return result.returncode


if __name__ == "__main__":
    raise SystemExit(main())
