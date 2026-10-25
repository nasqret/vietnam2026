"""Register the weekend training recipes and freeze the unchanged trainer on SLURM."""
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import shutil


def pin(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def write(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, allow_nan=False) + '\n')


def main():
    if not os.environ.get('SLURM_JOB_ID'):
        raise SystemExit('Registration requires SLURM')
    root = Path.cwd().resolve()
    old = root/'releases/campaign5-main-v1'
    old_manifest = old/'release-manifest.json'
    if pin(old_manifest) != '858f8a7d23eafb83e08038028263dbc5bf9442e2c57238992251d9068cdac87a':
        raise RuntimeError('Validated Campaign 5 release changed')
    inventory = json.loads(old_manifest.read_text())['files_sha256']
    for name, digest in inventory.items():
        if pin(old/name) != digest:
            raise RuntimeError('Frozen source changed: '+name)
    release = root/'releases/campaign6-training-v1'
    if release.exists():
        raise RuntimeError('Training release must be new')
    release.mkdir(parents=True)
    for name in inventory:
        if name.startswith('src/latentproof/'):
            target = release/name
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(old/name, target)
    # The model/checker implementation is byte-identical to the validated source.
    import sys
    sys.path.insert(0, str(release/'src'))
    from latentproof.campaign5_training import checked_options
    from latentproof.qwen_finalize_v2 import checked_protocol, training_object_digest
    base = json.loads((old/'configs/campaign5-main.json').read_text())
    previous_protocol = json.loads((old/'configs/campaign5-main-finalization.json').read_text())
    values, runs = {}, []
    for group, steps, milestones in (
            ('main', 8192, [1024, 2048, 4096, 8192]),
            ('long-vanilla', 24576, [8192, 12288, 16384, 24576])):
        cfg = json.loads(json.dumps(base))
        cfg.update(campaign_id='qwen-c6-'+group+'-20261017',
                   title='Weekend Qwen '+group, steps=steps,
                   train_seconds_limit=30*3600, evaluation_seconds_limit=8*3600,
                   generation_seconds_per_event=2*3600, eval_every=256,
                   checkpoint_every=128, log_every=10)
        cfg['campaign5']['proof_eval_steps'] = milestones
        if group == 'long-vanilla':
            cfg['arms'] = ['qwen_vanilla']
            cfg['campaign5']['selection_policies'] = {'qwen_vanilla': {'kind':'fixed','depth':1}}
        for arm in cfg['arms']:
            checked_options(cfg, arm)
        name = 'configs/campaign6-'+group+'.json'
        values[name] = cfg
        registered = []
        for seed in cfg['seeds']:
            for arm in cfg['arms']:
                run_id = f'helios-c6-{group}-{arm}-s{seed}'
                registered.append({'run_id':run_id,'arm':arm,'seed':seed})
                runs.append({'run_id':run_id,'arm':arm,'seed':seed,'group':group,
                    'config':name,'steps':steps,'directory':'artifacts/campaign6/runs/'+run_id})
        protocol = {**previous_protocol, 'campaign_id':cfg['campaign_id'],
            'protocol_id':'qwen-c6-'+group+'-primary-v1',
            'training_config_object_sha256':training_object_digest(cfg),
            'registered_arms':cfg['arms'],'runs':registered,
            'policies_by_arm':{arm:previous_protocol['policies_by_arm'][arm] for arm in cfg['arms']}}
        checked_protocol(protocol)
        values['configs/campaign6-'+group+'-finalization.json'] = protocol
    for name, value in values.items():
        write(release/name, value)
        write(root/name, value)
    for name in ('scripts/campaign6_worker.py','scripts/campaign6_recovery.py','slurm/campaign6-helios.sbatch',
                 'research/campaign6-weekend-protocol.md'):
        target = release/name
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(root/name, target)
    frozen = {str(p.relative_to(release)):pin(p) for p in sorted(release.rglob('*')) if p.is_file()}
    manifest = {'format':'latent-campaign6-training-release-v1','name':release.name,
        'created_at':datetime.now(timezone.utc).isoformat(),'job_id':os.environ['SLURM_JOB_ID'],
        'validated_parent_manifest_sha256':pin(old_manifest),'trainer_source_unchanged':True,
        'files_sha256':frozen,'checkpoints_included':False}
    write(release/'release-manifest.json',manifest)
    manifest_pin = pin(release/'release-manifest.json')
    for run in runs:
        run['config_sha256'] = frozen[run['config']]
    registration = {'format':'latent-campaign6-registration-v1','state':'registered',
        'created_at':manifest['created_at'],'job_id':os.environ['SLURM_JOB_ID'],
        'training_release':str(release),'training_release_manifest_sha256':manifest_pin,
        'data_directory':'data/processed/campaign5-bpe-v2','runs':runs,
        'max_allocated_gpu_hours':1280,'max_allocated_cpu_hours':256,
        'initial_training_workers':15,'initial_evaluation_workers':12,
        'worker_wall_seconds':144000,'automatic_replenishment':False,
        'proof_tier':'T4','review_state':'pending-results',
        'protocol_sha256':pin(root/'research/campaign6-weekend-protocol.md')}
    write(root/'artifacts/campaign6/registration.json',registration)
    write(root/'artifacts/campaign6/releases/training-manifest.json',manifest)
    write(root/'configs/campaign6-weekend.json',registration)
    print(json.dumps({'state':'registered','training_runs':len(runs),
        'release_manifest_sha256':manifest_pin,'registration_sha256':pin(root/'artifacts/campaign6/registration.json')}))


if __name__ == '__main__':
    main()
