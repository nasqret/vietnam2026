"""Actual 1.7B weekend recipe/shape and exact random-depth restart gate (SLURM)."""
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import subprocess
import sys
import time

from campaign6_worker import atomic, digest, verify_release


def equal(left, right):
    import torch
    if torch.is_tensor(left):
        assert torch.is_tensor(right) and left.dtype == right.dtype and left.shape == right.shape
        assert torch.equal(left,right)
    elif isinstance(left,dict):
        assert isinstance(right,dict) and left.keys() == right.keys()
        for key in left:
            equal(left[key],right[key])
    elif isinstance(left,(list,tuple)):
        assert type(left) is type(right) and len(left) == len(right)
        for a,b in zip(left,right):
            equal(a,b)
    else:
        assert type(left) is type(right) and left == right


def main():
    if not os.environ.get('SLURM_JOB_ID'):
        raise SystemExit('SLURM required')
    import torch
    root = Path.cwd().resolve()
    project = Path(os.environ['LATENT_PROJECT_ROOT'])
    pin = os.environ['LATENT_RELEASE_SHA256']
    verify_release(root,pin)
    out = project/'artifacts/campaign6/smoke'/os.environ['SLURM_JOB_ID']
    out.mkdir(parents=True,exist_ok=False)
    result = {'state':'running','job_id':os.environ['SLURM_JOB_ID'],
        'training_release_manifest_sha256':pin,'gpu':torch.cuda.get_device_name(0),
        'started_at':datetime.now(timezone.utc).isoformat(),'phases':[],
        'preflight_sha256':digest(__file__),'batch_sha256':digest(project/'slurm/campaign6-preflight.sbatch')}
    public = project/'artifacts/campaign6/validation'/os.environ['SLURM_JOB_ID']
    public.mkdir(parents=True,exist_ok=False)
    atomic(public/'validation.json',result)
    cfg = root/'configs/campaign6-main.json'
    started = time.monotonic()
    phases = [('qwen_vanilla','vanilla',2),('qwen_fixed','fixed',2),
              ('qwen_adaptive','adaptive',2),('qwen_random','random-fresh',4),
              ('qwen_random','random-resumed',2),('qwen_random','random-resumed',4)]
    for i,(arm,name,step) in enumerate(phases):
        target = out/name
        command = [sys.executable,'-m','latentproof.qwen_train','--config',str(cfg),
            '--arm',arm,'--seed','11','--data',str(project/'data/processed/campaign5-bpe-v2'),
            '--model',os.environ['LATENT_BASE_MODEL'],'--peano-root',os.environ['LATENT_PEANO_ROOT'],
            '--out',str(target),'--cluster','helios','--stop-after-step',str(step)]
        with (out/f'phase-{i}.out').open('w') as stdout,(out/f'phase-{i}.err').open('w') as stderr:
            child = subprocess.run(command,stdout=stdout,stderr=stderr,timeout=1800,check=False)
        assert child.returncode == 0, f'phase {i} failed'
        state = json.loads((target/'status.json').read_text())
        assert state['state'] == 'budget_limited' and state['step'] == step
        result['phases'].append({'arm':arm,'run':name,'step':step,'state':state['state']})
        atomic(public/'validation.json',result)
    a = torch.load(out/'random-fresh/last.pt',map_location='cpu',weights_only=False)
    b = torch.load(out/'random-resumed/last.pt',map_location='cpu',weights_only=False)
    fields = ('identity','step','trainable','optimizer','stream','depth_rng','torch_rng','cuda_rng',
              'tokens_seen','examples_seen','training_forward')
    for key in fields:
        equal(a[key],b[key])
    verify_release(root,pin)
    result.update(state='passed',elapsed_seconds=time.monotonic()-started,
        exact_restart_fields=list(fields),micro_batch_size=4,effective_batch_size=16,context_limit=6144,
        scope='Actual unchanged Qwen trainer at weekend recipe; four-arm updates and bitwise random-depth restart. Not a capability result.',
        finished_at=datetime.now(timezone.utc).isoformat())
    atomic(public/'validation.json',result)
    print(json.dumps(result),flush=True)


if __name__ == '__main__':
    main()
