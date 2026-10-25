"""One CPU-only admission of the exact transferred portable dataset; no GPU."""
from pathlib import Path
import json
import shlex
import subprocess
import time

from stage_p6_remote import SSH

HERE = Path(__file__).resolve().parent
OUT = HERE / "p6-linux-data-admission-v2-01"
SOURCE = "/net/scratch/hscra/plgrid/plgnasqret/codex-control/projects/peano-lab-training/experiments/hydra-practical-v1-20260904/bundles/source-data-03/source"
EXPECTED_PLAN = "0d4a80e91aba0dedfb3b8f4434540ab687e7361375268c4ebfd62e815719dd4e"
REMOTE = r'''
import json,os,resource,signal,sys,time
from pathlib import Path
resource.setrlimit(resource.RLIMIT_CPU,(45,45))
resource.setrlimit(resource.RLIMIT_AS,(2*1024**3,2*1024**3))
signal.alarm(60)
started=time.monotonic()
source=Path(SOURCE)
output=source.parents[2]/'jobs/p6-linux-data-admission-v2-01'
output.mkdir(parents=True,exist_ok=False)
os.chdir(source)
sys.path[:0]=[str(source/'hydra-playground'),str(source/'hydra-playground/native-v7'),str(source/'hydra-playground/training-v5')]
from hydra_training_v5.decision_pilot import prepare
plan=prepare('hydra-playground/training-v5/configs/qwen3_4b_decisions_v2_pilot.toml',
 dataset_manifest='output/hydra-implementation-2026-09-04/decisions-v2-01/manifest.json',
 dataset_sha256='e575970df58d046735f492acaf22e1cdea44445608a201c62d0644590b95ea77',
 failure_output=output/'failure-evidence')
(output/'prepared-pilot.json').write_text(json.dumps(plan.record,indent=2)+'\n')
matched=plan.record['plan_sha256']==EXPECTED_PLAN
record={'schema':'hydra-linux-data-admission-v2','completed':True,'exact_plan_match':matched,
 'plan_sha256':plan.record['plan_sha256'],'training_rows':plan.record['training_rows'],
 'optimizer_steps':plan.record['expected_optimizer_steps'],'data_attestation':plan.record['data_attestation'],
 'elapsed_seconds':time.monotonic()-started,'peak_rss_bytes':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss*1024,
 'python':sys.version,'cpu_seconds_ceiling':45,'wall_seconds_ceiling':60,'address_space_bytes_ceiling':2*1024**3,
 'model_calls':0,'native_proof_replays':0,'gpu_allocations':0,'automatic_retry':False,'remote_output':str(output)}
(output/'result.json').write_text(json.dumps(record,indent=2)+'\n')
print(json.dumps(record),flush=True)
assert matched,'Portable dataset/config plan differs on Linux'
'''


def main():
    OUT.mkdir(exist_ok=False)
    source = "SOURCE=" + repr(SOURCE) + "\nEXPECTED_PLAN=" + repr(EXPECTED_PLAN) + "\n" + REMOTE
    (OUT / "remote-script.py").write_text(source)
    base = "/net/software/x86_64/el8/Python/3.11.5-GCCcore-13.2.0"
    command = ["env", "PYTHONHASHSEED=20260904", "PYTHONDONTWRITEBYTECODE=1", "LD_LIBRARY_PATH=" + base + "/lib",
               base + "/bin/python3", "-B", "-P", "-c", source]
    began = time.monotonic()
    result = subprocess.run(SSH + [" ".join(shlex.quote(x) for x in command)],
                            stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=80)
    (OUT / "stdout.json").write_bytes(result.stdout)
    (OUT / "stderr.txt").write_bytes(result.stderr)
    receipt = {"actual_ssh_exit_code": result.returncode, "elapsed_seconds": time.monotonic()-began,
               "gpu_allocations": 0, "model_calls": 0, "automatic_retry": False}
    (OUT / "actual-completion.json").write_text(json.dumps(receipt, indent=2)+"\n")
    print(result.stdout.decode(), end="")
    print(result.stderr.decode(), end="")
    print(json.dumps(receipt), flush=True)
    return result.returncode


if __name__ == "__main__":
    raise SystemExit(main())
