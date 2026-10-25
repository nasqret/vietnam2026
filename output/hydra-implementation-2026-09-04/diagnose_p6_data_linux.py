"""One CPU-only regeneration of the failed frozen dataset; no GPU allocation."""
from pathlib import Path
import json
import shlex
import subprocess
import time

from stage_p6_remote import SSH

HERE=Path(__file__).resolve().parent
OUT=HERE/"p6-linux-data-diagnosis-01"
SOURCE="/net/scratch/hscra/plgrid/plgnasqret/codex-control/projects/peano-lab-training/experiments/hydra-practical-v1-20260904/bundles/source-data-02/source"
REMOTE=r'''
import json,os,resource,signal,sys,time
from pathlib import Path
resource.setrlimit(resource.RLIMIT_CPU,(45,45))
resource.setrlimit(resource.RLIMIT_AS,(2*1024**3,2*1024**3))
signal.alarm(60)
started=time.monotonic()
source=Path(SOURCE)
output=source.parents[2]/'jobs/p6-linux-data-diagnosis-01'
output.mkdir(parents=True,exist_ok=False)
os.chdir(source)
sys.path[:0]=[str(source/'hydra-playground'),str(source/'hydra-playground/native-v7'),str(source/'hydra-playground/training-v5')]
import proof_planner
import export_decisions
original_path=source/'output/hydra-implementation-2026-09-04/decisions-v1-02/manifest.json'
original=json.loads(original_path.read_bytes())
regenerated=export_decisions.export_dataset('hydra-playground/training-v5/configs/decision-inputs-v1.json',
 input_sha256='f21200dadbfae992a1fbb4095d724864ee1fefeae7104920aa2275fef14b6c07',output=output/'regenerated')
changed_fields=[key for key in sorted(set(original)|set(regenerated)) if original.get(key)!=regenerated.get(key)]
changed_files={name:{'original':pin,'regenerated':regenerated['files'].get(name)} for name,pin in original['files'].items() if pin!=regenerated['files'].get(name)}
examples=[];changed_rows=0;non_feature_changes=0
if 'ranker-train.jsonl' in changed_files:
 left=[json.loads(line)for line in (original_path.parent/'ranker-train.jsonl').read_bytes().splitlines()]
 right=[json.loads(line)for line in (output/'regenerated/ranker-train.jsonl').read_bytes().splitlines()]
 assert len(left)==len(right)
 for old,new in zip(left,right):
  if old==new:continue
  changed_rows+=1
  keys=[key for key in old if old[key]!=new.get(key)]
  if keys!=['features']:non_feature_changes+=1
  if len(examples)<3:examples.append({'id':old['id'],'changed_keys':keys,
   'features':{key:{'old':old['features'][key],'new':new['features'].get(key)}for key in old['features']if old['features'][key]!=new['features'].get(key)}})
record={'schema':'hydra-linux-data-regeneration-diagnosis-v1','completed':True,'exact_match':original==regenerated,
 'changed_manifest_fields':changed_fields,'changed_files':changed_files,'changed_ranking_rows':changed_rows,
 'ranking_changes_outside_features':non_feature_changes,'feature_examples':examples,
 'primitive_files_byte_identical':all(original['files'][name]==regenerated['files'][name]for name in ('primitive-train.jsonl','primitive-val.jsonl','primitive-test.jsonl')),
 'elapsed_seconds':time.monotonic()-started,'peak_rss_bytes':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss*1024,
 'python':sys.version,'cpu_seconds_ceiling':45,'wall_seconds_ceiling':60,'address_space_bytes_ceiling':2*1024**3,
 'model_calls':0,'native_proof_replays':0,'gpu_allocations':0,'automatic_retry':False,'remote_output':str(output)}
(output/'result.json').write_text(json.dumps(record,indent=2)+'\n')
print(json.dumps(record),flush=True)
'''


def main():
    OUT.mkdir(exist_ok=False)
    source="SOURCE="+repr(SOURCE)+"\n"+REMOTE
    (OUT/"remote-script.py").write_text(source)
    base="/net/software/x86_64/el8/Python/3.11.5-GCCcore-13.2.0"
    command=["env","PYTHONHASHSEED=20260904","PYTHONDONTWRITEBYTECODE=1","LD_LIBRARY_PATH="+base+"/lib",
             base+"/bin/python3","-B","-P","-c",source]
    began=time.monotonic()
    result=subprocess.run(SSH+[" ".join(shlex.quote(x)for x in command)],stdout=subprocess.PIPE,stderr=subprocess.PIPE,timeout=80)
    (OUT/"stdout.json").write_bytes(result.stdout)
    (OUT/"stderr.txt").write_bytes(result.stderr)
    receipt={"actual_ssh_exit_code":result.returncode,"elapsed_seconds":time.monotonic()-began,
             "gpu_allocations":0,"model_calls":0,"automatic_retry":False}
    (OUT/"actual-completion.json").write_text(json.dumps(receipt,indent=2)+"\n")
    if result.returncode==0:
        v=json.loads(result.stdout);print(json.dumps({k:v[k]for k in ('completed','exact_match','changed_manifest_fields','changed_files','changed_ranking_rows','ranking_changes_outside_features','primitive_files_byte_identical','elapsed_seconds','peak_rss_bytes')}))
    else:print(result.stderr.decode(),end="")
    print(json.dumps(receipt),flush=True)
    return result.returncode


if __name__=="__main__":raise SystemExit(main())
