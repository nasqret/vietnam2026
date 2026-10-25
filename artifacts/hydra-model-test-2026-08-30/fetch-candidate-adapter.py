"""Fetch two exact saved adapter files for local CPU provenance validation.

Read-only on Helios. Reuse eight already-present exact local artifact files;
never download a base model, import model frameworks, or submit a job.
"""
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import resource
import selectors
import shutil
import signal
import subprocess
import time

ROOT=Path('/Users/bnaskrecki/codex/peano')
ARCHIVE=ROOT/'artifacts/hydra-model-test-2026-08-30'
OUT=ARCHIVE/'candidate-model'
RECEIPT=ARCHIVE/'candidate-model-fetch-01.json'
BASELINE=ROOT/'_deploy/hydra-search-v2-build-20260829/_deploy/hydra-search-v2/model'
TRAINING=ROOT/'artifacts/frontier-training-2026-08-30'
REMOTE='plgnasqret@helios.cyfronet.pl:/net/scratch/hscra/plgrid/plgnasqret/codex-control/projects/peano-lab-training/experiments/frontier-training-v1/results/peano-hydra/qwen3-1.7b-authority-primitive-v28-f64b5f100c9c-frontier-training-v1/'
FETCH=('adapter/adapter_config.json','adapter/adapter_model.safetensors')
MAX_FILE=80*1024**2


def identity(path):
    if path.is_symlink() or not path.is_file() or path.stat().st_size>MAX_FILE:
        raise ValueError('Unexpected artifact file: '+str(path))
    digest=hashlib.sha256()
    with path.open('rb') as stream:
        while True:
            raw=stream.read(1024**2)
            if not raw:break
            digest.update(raw)
    return {'bytes':path.stat().st_size,'sha256':digest.hexdigest()}


def main():
    if OUT.exists() or RECEIPT.exists():raise ValueError('Fresh local destinations required')
    resource.setrlimit(resource.RLIMIT_CPU,(20,21))
    resource.setrlimit(resource.RLIMIT_CORE,(0,0))
    resource.setrlimit(resource.RLIMIT_FSIZE,(MAX_FILE,MAX_FILE))
    started=time.monotonic()
    record={'schema':'peano-hydra-candidate-adapter-local-fetch-v1',
        'started_at_utc':datetime.now(timezone.utc).isoformat(),
        'status':'incomplete','remote_writes':False,'gpu_job_submitted':False,
        'model_frameworks_imported':False,'base_model_downloaded':False,
        'automatic_retry':False,'output_root':str(OUT),
        'limits':{'cpu_seconds':20,'wall_seconds':120,'maximum_single_file_bytes':MAX_FILE,
            'expected_remote_bytes':69783287,'expected_model_directory_bytes':89040031}}
    raw=(TRAINING/'completed-artifacts-01/receipt.json').read_bytes()
    if hashlib.sha256(raw).hexdigest()!='6af7c587bf87b956ad31addaa45617cb6e0fa8db3f74c462b2b80619b3b59ffc':
        raise ValueError('Independent remote artifact inventory changed')
    pins=json.loads(raw)['artifact_files']
    manifest=(TRAINING/'completed-manifest-01.json').read_bytes()
    if hashlib.sha256(manifest).hexdigest()!='5795d5a3d70f781f56f81e83c2295c887d0949795924f4208f45d26a3ef89b68':
        raise ValueError('Completed model manifest changed')
    if len(pins)!=10 or sum(p['bytes'] for p in pins.values())!=85670667:
        raise ValueError('Artifact count or total differs')
    for name,pin in pins.items():
        if name not in FETCH and identity(BASELINE/name)!=pin:
            raise ValueError('Existing reusable artifact differs: '+name)
    if shutil.disk_usage(ARCHIVE).free<89040031+1024**3:
        raise ValueError('Insufficient free disk plus reserve')
    OUT.mkdir(mode=0o700)
    (OUT/'adapter').mkdir(mode=0o700)
    (OUT/'tokenizer').mkdir(mode=0o700)
    with (OUT/'manifest.json').open('xb') as stream:stream.write(manifest)
    for name,pin in pins.items():
        if name not in FETCH:
            with (BASELINE/name).open('rb') as src,(OUT/name).open('xb') as dst:
                shutil.copyfileobj(src,dst,1024**2)
    options=['BatchMode=yes','ConnectTimeout=15','ServerAliveInterval=10','ServerAliveCountMax=2',
        'ForwardAgent=no','ClearAllForwardings=yes','StrictHostKeyChecking=yes','UpdateHostKeys=no',
        'ControlMaster=no','ControlPath=none']
    command=['/usr/bin/scp','-q']
    for option in options:command.extend(['-o',option])
    command.extend(['--',*(REMOTE+name for name in FETCH),str(OUT/'adapter')+'/'])
    record['command']=command
    process=None;selector=selectors.DefaultSelector();streams={'stdout':bytearray(),'stderr':bytearray()}
    try:
        process=subprocess.Popen(command,stdin=subprocess.DEVNULL,stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,start_new_session=True)
        for label,pipe in [('stdout',process.stdout),('stderr',process.stderr)]:
            os.set_blocking(pipe.fileno(),False);selector.register(pipe,selectors.EVENT_READ,label)
        while selector.get_map() or process.poll() is None:
            if time.monotonic()-started>120:raise TimeoutError('Adapter read-only transfer deadline')
            for key,_ in selector.select(0.1):
                chunk=os.read(key.fileobj.fileno(),65536)
                if not chunk:selector.unregister(key.fileobj);continue
                streams[key.data].extend(chunk)
                if sum(map(len,streams.values()))>256*1024:raise ValueError('Transport log bound exceeded')
        process.wait(timeout=1)
        record['returncode']=process.returncode
        if process.returncode!=0:raise ValueError('Read-only adapter transfer did not complete')
        found={p.relative_to(OUT).as_posix() for p in OUT.rglob('*') if p.is_file()}
        if found!=set(pins)|{'manifest.json'}:raise ValueError('Local model directory inventory differs')
        observed={name:identity(OUT/name) for name in pins}
        if observed!=pins:raise ValueError('Fetched/copied artifact bytes differ from original pins')
        record.update(status='exact-saved-artifacts-available-locally',files=observed,
            manifest={'bytes':len(manifest),'sha256':hashlib.sha256(manifest).hexdigest()},
            downloaded_files=list(FETCH),downloaded_bytes=sum(pins[n]['bytes'] for n in FETCH),
            copied_existing_local_files=8,copied_existing_local_bytes=15887380)
    except BaseException as error:
        record.update(error_type=type(error).__name__,error=str(error)[:2048])
    finally:
        if process is not None:
            if process.poll() is None:
                os.killpg(process.pid,signal.SIGKILL);process.wait(timeout=5)
            process.stdout.close();process.stderr.close()
        selector.close()
    record['transport_logs']={k:bytes(v).decode('utf-8','replace') for k,v in streams.items()}
    usage=resource.getrusage(resource.RUSAGE_SELF)
    record['resources']={'wall_seconds':time.monotonic()-started,
        'self_cpu_seconds':usage.ru_utime+usage.ru_stime,'self_peak_rss_bytes':usage.ru_maxrss}
    record['finished_at_utc']=datetime.now(timezone.utc).isoformat()
    output=(json.dumps(record,sort_keys=True,indent=2,allow_nan=False)+'\n').encode()
    with RECEIPT.open('xb') as stream:stream.write(output)
    print(json.dumps({'status':record['status'],'receipt':str(RECEIPT),
        'sha256':hashlib.sha256(output).hexdigest(),'downloaded_bytes':record.get('downloaded_bytes'),
        'resources':record['resources'],'error':record.get('error')},sort_keys=True))
    return 0 if record['status']=='exact-saved-artifacts-available-locally' else 1


if __name__=='__main__':raise SystemExit(main())
