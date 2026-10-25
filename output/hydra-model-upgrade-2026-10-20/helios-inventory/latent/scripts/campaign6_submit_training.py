"""One-shot bounded submission of the 15 registered weekend training workers."""
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import subprocess
from campaign6_worker import atomic, digest, verify_release

if not os.environ.get('SLURM_JOB_ID'):
    raise SystemExit('Registration/submission requires SLURM')
root = Path('/net/scratch/hscra/plgrid/plgnasqret/latent')
registration_path = root/'artifacts/campaign6/registration.json'
registration = json.loads(registration_path.read_text())
release = Path(registration['training_release'])
verify_release(release,registration['training_release_manifest_sha256'])
if (root/'artifacts/campaign6/training-submission.json').exists():
    raise RuntimeError('Training wave already registered; no automatic replenishment')
for job in ('24776281','24775629'):
    gate = json.loads((root/'artifacts/campaign6/validation'/job/'validation.json').read_text())
    if gate['state'] != 'passed':
        raise RuntimeError('Preflight gate failed: '+job)
    if job == '24775629' and gate['training_release_manifest_sha256'] != registration['training_release_manifest_sha256']:
        raise RuntimeError('Preflight used another training release')
recovery_gate = root/'artifacts/campaign6/validation/24779085'
if 'OK' not in (recovery_gate/'recovery-tests.txt').read_text():
    raise RuntimeError('Independent recovery test evidence missing')
tested_helper = next(line.split()[0] for line in (recovery_gate/'inputs.sha256').read_text().splitlines()
    if line.endswith('scripts/campaign6_recovery.py'))
if tested_helper != digest(release/'scripts/campaign6_recovery.py'):
    raise RuntimeError('Tested recovery helper differs from frozen training worker dependency')
ledger_path = root/'status/campaign6.json'
ledger = json.loads(ledger_path.read_text())
gpu_seconds = sum(job['gpus']*job['wall_limit_seconds'] for job in ledger['jobs'])
if gpu_seconds+len(registration['runs'])*144000 > ledger['max_allocated_gpu_hours']*3600:
    raise RuntimeError('Requested GPU envelope exceeded')
receipt = {'state':'submitting-held','job_id':os.environ['SLURM_JOB_ID'],
    'registration_sha256':digest(registration_path),'jobs':[],'automatic_replenishment':False}
registry = {'schema_version':1,'campaign':{'id':'qwen-campaign6-weekend-20261017',
    'title':'Weekend: Qwen3-1.7B recurrence at scale',
    'objective':'Complete paired proof/cost comparisons; three seeds, 8192-update main arms and longer vanilla controls.'},
    'runs':[],'notes':['T4; live observations are not independently reviewed results.',
        'Main8192 and vanilla24576 have separately registered cosine schedules; report cost frontiers, not exact compute matching.']}
for index,task in enumerate(registration['runs']):
    env = dict(os.environ,LATENT_RELEASE=str(release),
        LATENT_RELEASE_SHA256=registration['training_release_manifest_sha256'],
        LATENT_REGISTRATION_SHA256=digest(registration_path),LATENT_TRAIN_INDEX=str(index),
        LATENT_WORKER_SECONDS='143100')
    job = subprocess.check_output(['sbatch','--hold','--parsable','--export=ALL',
        '--job-name=latent-c6-'+task['group']+'-'+task['arm'].removeprefix('qwen_')+'-'+str(task['seed']),
        str(release/'slurm/campaign6-helios.sbatch')],cwd=root,env=env,text=True).strip().split(';')[0]
    if not job.isdigit():
        raise RuntimeError('Unexpected scheduler identity')
    binding = {'cluster':'helios','job_id':job,'role':'training-and-evaluation-tail',
        'run_id':task['run_id'],'gpus':1,'cpus':4,'memory_gib':96,
        'wall_limit_seconds':144000,'state':'held',
        'source_manifest_sha256':registration['training_release_manifest_sha256']}
    ledger['jobs'].append(binding)
    receipt['jobs'].append(binding)
    registry['runs'].append({'run_id':task['run_id'],'campaign_id':registry['campaign']['id'],
        'cluster':'helios','arm':task['arm'],'seed':task['seed'],'job_id':job,
        'state':'queued','step':0,'max_steps':task['steps'],'role':task['group'],
        'execution_mode':'dedicated-worker','directory':str(root/task['directory']),
        'dispatch_file':'artifacts/campaign6/task-status/'+task['run_id']+'.json',
        'notes':['Selected checkpoints must satisfy development-only selection; incomplete schedules are explicit.']})
    atomic(ledger_path,ledger)
    atomic(root/'artifacts/campaign6/training-submission.json',receipt)
    atomic(root/'artifacts/campaign6/registry.json',registry)
for binding in receipt['jobs']:
    subprocess.run(['scontrol','release',binding['job_id']],check=True)
    binding['state'] = 'released'
ledger['state'] = 'training-wave-submitted'
ledger['updated_at'] = datetime.now(timezone.utc).isoformat()
atomic(ledger_path,ledger)
receipt.update(state='submitted',submitted_at=ledger['updated_at'])
atomic(root/'artifacts/campaign6/training-submission.json',receipt)
print(json.dumps(receipt),flush=True)
