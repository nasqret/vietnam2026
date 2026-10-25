"""Finite weekend training worker with owned process groups and exact-state retries.

No scheduler submissions or allocation replenishment. Computation runs in SLURM.
Training uses a byte-identical Campaign 5 source tree in its immutable release.
"""
from datetime import datetime, timezone
import fcntl
import hashlib
import json
import os
from pathlib import Path
import signal
import subprocess
import sys
import time


def now():
    return datetime.now(timezone.utc).isoformat()


def digest(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as f:
        for block in iter(lambda:f.read(1024*1024), b''):
            h.update(block)
    return h.hexdigest()


def atomic(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_suffix('.'+str(os.getpid())+'.tmp')
    temp.write_text(json.dumps(value, indent=2, allow_nan=False)+'\n')
    temp.replace(path)


def verify_release(root, expected):
    path = root/'release-manifest.json'
    if digest(path) != expected:
        raise RuntimeError('Unregistered training release')
    manifest = json.loads(path.read_text())
    for name, pin in manifest['files_sha256'].items():
        target = (root/name).resolve()
        if not target.is_relative_to(root) or digest(target) != pin:
            raise RuntimeError('Changed training release: '+name)
    return manifest


def prepare_resume(directory, cfg, task, data, model_path):
    """Preserve uncommitted proof output before an exact optimizer-state replay."""
    import torch
    import transformers
    import peft
    from campaign6_recovery import archive_uncommitted_evaluations, object_digest
    receipt = json.loads((directory/'receipt.json').read_text())
    data_hashes = {}
    for name, expected in receipt['identity']['data'].items():
        path = (data/name).resolve()
        if not path.is_relative_to(data) or digest(path) != expected:
            raise RuntimeError('Resume corpus changed')
        data_hashes[name] = digest(path)
    base = {name:digest(model_path/name) for name in cfg['base_files_sha256']}
    if base != cfg['base_files_sha256']:
        raise RuntimeError('Resume base weights changed')
    expected_identity = {'arm':task['arm'],'seed':task['seed'],'config_sha256':object_digest(cfg),
        'data':data_hashes,'base':base,
        'sources_sha256':{str(p):digest(p) for p in sorted(Path('src/latentproof').glob('*.py'))},
        'transformers':transformers.__version__,'peft':peft.__version__,
        'torch':str(torch.__version__),'cuda':torch.version.cuda,
        'device':torch.cuda.get_device_name(0),
        'deterministic_algorithms':bool(cfg.get('deterministic_algorithms',True)),
        'cublas_workspace_config':os.environ.get('CUBLAS_WORKSPACE_CONFIG')}
    checkpoint_pin = digest(directory/'last.pt')
    saved = torch.load(directory/'last.pt',map_location='cpu',weights_only=False)
    archive_uncommitted_evaluations(directory,saved=saved,checkpoint_sha256=checkpoint_pin,
        expected_identity=expected_identity,expected_total_steps=cfg['steps'])
    return saved['step']


def main():
    if not os.environ.get('SLURM_JOB_ID'):
        raise SystemExit('Weekend execution requires SLURM')
    root, project = Path.cwd().resolve(), Path(os.environ['LATENT_PROJECT_ROOT']).resolve()
    job = os.environ['SLURM_JOB_ID']
    release_pin = os.environ['LATENT_RELEASE_SHA256']
    verify_release(root, release_pin)
    registration_path = project/'artifacts/campaign6/registration.json'
    if digest(registration_path) != os.environ['LATENT_REGISTRATION_SHA256']:
        raise RuntimeError('Registration changed')
    registration = json.loads(registration_path.read_text())
    index = int(os.environ['LATENT_TRAIN_INDEX'])
    task = registration['runs'][index]
    if registration['training_release_manifest_sha256'] != release_pin:
        raise RuntimeError('Registration/release mismatch')
    directory = project/task['directory']
    if not directory.resolve().is_relative_to(project/'artifacts/campaign6/runs'):
        raise RuntimeError('Output escapes this campaign')
    cfg_path = root/task['config']
    if digest(cfg_path) != task['config_sha256']:
        raise RuntimeError('Training configuration changed')
    cfg = json.loads(cfg_path.read_text())
    run_id = task['run_id']
    receipt_path = project/'artifacts/campaign6/workers'/('train-'+job+'.json')
    dispatch_path = project/'artifacts/campaign6/task-status'/(run_id+'.json')
    stopped = [False]
    def stop(*_):
        stopped[0] = True
    for sig in (signal.SIGUSR1, signal.SIGTERM, signal.SIGINT):
        signal.signal(sig, stop)
    start = time.monotonic()
    maximum = min(int(os.environ.get('LATENT_WORKER_SECONDS','143100')),143100)
    deadline = start+maximum
    receipt = {'format':'latent-campaign6-training-worker-v1','job_id':job,'run_id':run_id,
        'release_manifest_sha256':release_pin,'registration_sha256':digest(registration_path),
        'started_at':now(),'state':'initializing','attempts':[],'max_attempts':2,
        'automatic_replenishment':False,'maximum_seconds':maximum}
    def update(**values):
        receipt.update(values,updated_at=now(),elapsed_seconds=time.monotonic()-start)
        atomic(receipt_path,receipt)
        atomic(dispatch_path,{key:receipt[key] for key in ('run_id','job_id','state','updated_at')})
    locks = project/'artifacts/campaign6/locks'
    locks.mkdir(parents=True,exist_ok=True)
    with (locks/(run_id+'.lock')).open('a') as lock:
        fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        for attempt in range(1,3):
            if stopped[0] or deadline-time.monotonic() < 900:
                update(state='budget_limited')
                break
            verify_release(root,release_pin)
            if directory.exists() and not (directory/'last.pt').exists():
                update(state='failed_no_resumable_checkpoint')
                break
            if (directory/'last.pt').exists():
                resume_step = prepare_resume(directory,cfg,task,
                    (project/registration['data_directory']).resolve(),Path(os.environ['LATENT_BASE_MODEL']))
            else:
                resume_step = 0
            record = {'number':attempt,'started_at':now(),'resume_step':resume_step}
            receipt['attempts'].append(record)
            command = [sys.executable,'-m','latentproof.qwen_train','--config',str(cfg_path),
                '--arm',task['arm'],'--seed',str(task['seed']),'--data',str(project/registration['data_directory']),
                '--model',os.environ['LATENT_BASE_MODEL'],'--peano-root',os.environ['LATENT_PEANO_ROOT'],
                '--out',str(directory),'--cluster','helios']
            log_dir = project/'artifacts/campaign6/logs'
            log_dir.mkdir(parents=True,exist_ok=True)
            update(state='running')
            with (log_dir/(run_id+'.out')).open('a') as stdout, (log_dir/(run_id+'.err')).open('a') as stderr:
                process = subprocess.Popen(command,stdout=stdout,stderr=stderr,start_new_session=True)
                while process.poll() is None:
                    if stopped[0] or time.monotonic() >= deadline-600:
                        os.killpg(process.pid,signal.SIGUSR1)
                        try:
                            process.wait(timeout=480)
                        except subprocess.TimeoutExpired:
                            os.killpg(process.pid,signal.SIGKILL)
                            process.wait()
                        break
                    time.sleep(2)
            state = json.loads((directory/'status.json').read_text()) if (directory/'status.json').exists() else {}
            record.update(exit_code=process.returncode,finished_at=now(),producer_state=state.get('state'),step=state.get('step'))
            verify_release(root,release_pin)
            if process.returncode == 0 and state.get('state') == 'completed' and state.get('step') == cfg['steps']:
                from campaign6_recovery import assess_milestones
                producer = json.loads((directory/'receipt.json').read_text())
                schedule = assess_milestones(directory,proof_eval_steps=cfg['campaign5']['proof_eval_steps'],
                    attained_step=state['step'],expected_roster=producer['campaign5']['proof_selection_roster'],
                    expected_policy=cfg['campaign5']['selection_policies'][task['arm']])
                atomic(directory/'selection-schedule.json',schedule)
                update(state='completed',training_completed=True,
                    selection_schedule_complete=schedule['selection_schedule_complete'],
                    primary_comparison_eligible=schedule['selection_schedule_complete'],
                    step=state['step'],max_steps=cfg['steps'])
                break
            if stopped[0] or state.get('state') == 'budget_limited':
                update(state='budget_limited',step=state.get('step'))
                break
            # Integrity/model exceptions are deterministic failures, not retryable
            # infrastructure events. Only a signal-killed process with an atomic
            # last.pt is eligible for one in-allocation restart.
            if (process.returncode not in {-9,-15,-10,137,143}
                    or (directory/'resume-failure.json').exists()
                    or not (directory/'last.pt').is_file()):
                update(state='failed',step=state.get('step'),retry_reason='not-a-retryable-interruption')
                break
            update(state='retry_pending' if attempt < 2 else 'failed',step=state.get('step'))
        training_state = receipt['state']
        update(training_state=training_state)
    # Independent evaluation work can continue even when this training run failed.
    # The launch file is registered separately after the evaluation source gate.
    launcher = project/'artifacts/campaign6/evaluation-launch.json'
    if not stopped[0] and deadline-time.monotonic() > 900 and launcher.is_file():
        launch = json.loads(launcher.read_text())
        release = Path(launch['release']).resolve()
        verify_release(release,launch['release_manifest_sha256'])
        env = dict(os.environ, LATENT_EVALUATION_LAUNCH_SHA256=digest(launcher),
            LATENT_WORKER_SECONDS=str(int(deadline-time.monotonic()-300)))
        env['PYTHONPATH'] = os.pathsep.join([str(project/'.helios-c3-deps'),str(release/'src'),str(project/'.helios-deps')])
        command = [sys.executable,str(release/'scripts/campaign6_eval_pool.py')]
        with (project/'artifacts/campaign6/logs'/('eval-tail-'+job+'.out')).open('a') as stdout:
            process = subprocess.Popen(command,cwd=release,env=env,stdout=stdout,stderr=subprocess.STDOUT,start_new_session=True)
            while process.poll() is None:
                if stopped[0] or time.monotonic() >= deadline-120:
                    os.killpg(process.pid,signal.SIGTERM)
                    try:
                        process.wait(timeout=90)
                    except subprocess.TimeoutExpired:
                        os.killpg(process.pid,signal.SIGKILL)
                        process.wait()
                    break
                time.sleep(2)
        update(evaluation_tail_exit_code=process.returncode)
    update(finished_at=now())
    print(json.dumps(receipt),flush=True)
    if training_state.startswith('failed'):
        raise SystemExit(1)


if __name__ == '__main__':
    main()
