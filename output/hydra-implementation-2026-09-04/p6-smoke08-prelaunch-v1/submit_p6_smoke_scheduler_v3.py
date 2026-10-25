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
OUT = HERE / "p6-smoke-4b-08"
PROJECT = "/net/scratch/hscra/plgrid/plgnasqret/codex-control/projects/peano-lab-training"
CAMPAIGN = PROJECT + "/experiments/hydra-practical-v1-20260904"
SOURCE = CAMPAIGN + "/bundles/source-data-07/source"
JOB = CAMPAIGN + "/jobs/p6-smoke-4b-08"
NAME = "hydra-p6-smoke-4b-08"


def main():
    cpu_path = HERE / "p6-cpu-prerequisite-01.json"
    cpu_raw = cpu_path.read_bytes()
    cpu_gate = json.loads(cpu_raw)
    assert cpu_gate["schema"] == "hydra-p6-actual-cpu-prerequisite-v1"
    assert cpu_gate["scheduler_helper_sha256"] == "cc8dec7bcb2187568c1aed1eaa1b580435460e297573b655eac2b32b74a271b4"
    assert cpu_gate["completed"] and cpu_gate["positive_proof_replayed"]
    assert cpu_gate["negative_probe_rejected"] and cpu_gate["owned_cleanup_verified"]
    assert cpu_gate["actual_process_exit_code"] == 0 and cpu_gate["actual_scheduler_exit"] == "0:0"
    assert cpu_gate["actual_scheduler_query_exit_code"] == 0
    assert len(cpu_gate["evidence_files"]) >= 3
    for relative, digest in cpu_gate["evidence_files"].items():
        target = (HERE / relative).resolve()
        assert target.is_relative_to(HERE.resolve()) and target.is_file() and not target.is_symlink()
        assert hashlib.sha256(target.read_bytes()).hexdigest() == digest
    transfer = json.loads((HERE / "p6-transfer-06/actual-completion.json").read_bytes())
    assert transfer["actual_ssh_exit_code"] == 0
    admission = json.loads((HERE / "p6-linux-data-admission-v2-01/stdout.json").read_bytes())
    assert admission["completed"] and admission["exact_plan_match"]
    assert admission["plan_sha256"] == "0d4a80e91aba0dedfb3b8f4434540ab687e7361375268c4ebfd62e815719dd4e"
    launch = json.loads((HERE / "p6-source-bundle-06/training-launch-inputs.json").read_bytes())
    bundle = json.loads((HERE / "p6-source-bundle-06/manifest.json").read_bytes())
    assert bundle["archive_sha256"] == transfer["archive_sha256"]
    assert bundle["files"]["hydra-playground/experimental_model.py"]["sha256"] == "7bacd4f97272093873db76ea7b2178e1074ca3ff5f2ef88b4e411933c131580f"
    assert bundle["files"]["output/p6-prototype/remote_provider_smoke.py"]["sha256"] == "cc8dec7bcb2187568c1aed1eaa1b580435460e297573b655eac2b32b74a271b4"
    assert launch["models"]["qwen3-4b-base"]["training_rows"] == 2047
    assert launch["models"]["qwen3-4b-base"]["expected_optimizer_steps"] == 256
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
        "prepared_plan_sha256":launch["models"]["qwen3-4b-base"]["plan_sha256"],
        "provider_sha256":"7bacd4f97272093873db76ea7b2178e1074ca3ff5f2ef88b4e411933c131580f",
        "cpu_prerequisite_sha256":hashlib.sha256(cpu_raw).hexdigest(),
        "scheduler_helper_sha256":"cc8dec7bcb2187568c1aed1eaa1b580435460e297573b655eac2b32b74a271b4",
        "submit_held":True, "source_layout":"Separately sealed bundle06 with unchanged decoder-v2 and the reviewed scheduler-v3 helper, materialized as new source-data-07; all old archives, source trees and failures preserved", "requeue":False, "automatic_retry":False,
        "submission_preflight_fix":"Attempt03 stopped before sbatch on compressed unrelated CPU job array IDs. Enumerate array elements and verify each exact ArrayJobId/ArrayTaskId and GPU TRES; leave all other jobs untouched.",
        "diagnosed_followup":"Job21911045 failed before model admission on the old combined wall/output scheduler guard. The reviewed helper now permits one query up to15seconds and records the exact failure reason, without retries or changes to identity,64KiB output,64successful-query cap,allocation or outer deadlines. Its23pure tests passed. A separate actual CPU fixture must pass the same scheduler query and native positive/negative/owned-cleanup checks before this held submission. Decoder v2 still requires actual GPU validation. This new one-use600second allocation keeps the same one theorem,two model calls,eight gradient examples,and zero optimizer updates. Original attempts remain unchanged."}
    (OUT / "allocation-request.json").write_text(json.dumps(spec, indent=2)+"\n")
    (OUT / "job.sbatch").write_text(script)
    campaign = json.loads((HERE / "campaign.json").read_bytes())
    reserved = campaign.get("gpu_seconds_reserved", round(campaign.get("gpu_hours_allocated",0)*3600))
    assert reserved + 600 <= campaign["campaign_gpu_hours_ceiling"] * 3600
    campaign["gpu_seconds_reserved"] = reserved + 600
    campaign.setdefault("gpu_reservations", []).append({"attempt":"p6-smoke-4b-08", "seconds":600,
        "gpus":1, "status":"prepared_for_held_submission", "request":"p6-smoke-4b-08/allocation-request.json"})
    (HERE / "campaign.json").write_text(json.dumps(campaign, indent=2)+"\n")
    remote = r'''
import hashlib,json,os,re,subprocess,sys
from pathlib import Path
os.umask(0o077)
request=json.loads(sys.stdin.read(128*1024))
spec=request['spec'];script=request['script']
assert hashlib.sha256(script.encode()).hexdigest()==spec['script_sha256']
directory=Path(spec['remote_job_directory'])
assert str(directory).endswith('/hydra-practical-v1-20260904/jobs/p6-smoke-4b-08')
queue=subprocess.run(['squeue','--array','-h','-u',str(os.getuid()),'-o','%i|%T|%j|%b'],stdout=subprocess.PIPE,stderr=subprocess.PIPE,universal_newlines=True,timeout=10)
assert queue.returncode==0 and len(queue.stdout.encode())<=16384
rows=queue.stdout.strip().splitlines();assert len(rows)<=32
observed=[]
for row in rows:
 job=row.split('|')[0].strip();assert re.fullmatch(r'[0-9]{1,20}(?:_[0-9]{1,10})?',job)
 query=subprocess.run(['scontrol','-o','show','job',job],stdout=subprocess.PIPE,stderr=subprocess.PIPE,universal_newlines=True,timeout=15)
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
