#!/usr/bin/env python3
"""Owner-authorized, additive deployment; backed-up navigation switches last."""
import argparse
import json
import os
from pathlib import Path
import resource
import shutil
import signal
from stage_sqrt2_power_research import encode,file_pin,inventory,pin,safe_path

PUBLIC=Path('/home/faculty/bnaskrecki/public_html/proofs')
RELEASE='research-releases/sqrt2-power-2026-10-11/manifest.json'
NAMESPACES=['sqrt2-power/checkpoints/2026-10-11','research-releases/sqrt2-power-2026-10-11']
ENTRANCES=('index.html','grand-campaign/index.html','sqrt2-power/index.html')
PARENTS=[dict(path='release-v35/manifest.json',sha256='6b11439683ec1d60baa0ea328536e1f8fb2d9057f362c3fe269f684894142756',field='current_files'),
         dict(path='research-releases/sqrt2-power-2026-10-01/manifest.json',sha256='d724b221ed1913924ed51ca444b0874b6cebd5fe00c3aeabcc1c6cf7a9a0d802',field='files')]


def activate(private, digest):
    if (private.parent!=Path('/home/faculty/bnaskrecki')
        or not private.name.startswith('.sqrt2-publication-') or private.is_symlink()
        or private.stat().st_uid!=os.getuid()):raise ValueError('Wrong private upload root')
    resource.setrlimit(resource.RLIMIT_CPU,(25,26));resource.setrlimit(resource.RLIMIT_AS,(512*1024**2,)*2);signal.alarm(120)
    payload=private/'payload';raw=safe_path(payload,RELEASE).read_bytes()
    if pin(raw)['sha256']!=digest:raise ValueError('Reviewed manifest changed')
    manifest=json.loads(raw)
    if (manifest['schema']!='sqrt2-power-research-delivery-v2' or manifest['new_library_admissions']!=0
        or manifest['published_supporting_statements']!=245 or manifest['namespaces']!=NAMESPACES
        or manifest['parent_manifests']!=PARENTS or set(manifest['replaced_navigation'])!=set(ENTRANCES)):
        raise ValueError('Unreviewed publication scope')
    files={**manifest['files'],RELEASE:pin(raw)};inventory(payload,files)
    if len(files)!=manifest['payload_file_count']:raise ValueError('Wrong file count')
    for name in files:
        if name not in ENTRANCES and not any(name.startswith(n+'/') for n in NAMESPACES):
            raise ValueError('Out-of-scope file')
    previous={}
    for parent in PARENTS:
        data=safe_path(PUBLIC,parent['path']).read_bytes()
        if pin(data)['sha256']!=parent['sha256']:raise ValueError('Public parent manifest changed')
        previous.update(json.loads(data)[parent['field']]);previous[parent['path']]=pin(data)
    for name,expected in previous.items():
        if file_pin(safe_path(PUBLIC,name))!=expected:raise ValueError('Public predecessor differs: '+name)
    for name in NAMESPACES:
        if safe_path(PUBLIC,name).exists():raise ValueError('Immutable namespace already exists')
    for name in set(files)-set(ENTRANCES):
        if name in previous:raise ValueError('Historical payload collision')
    backup=private/'rollback';backup.mkdir(mode=0o700)
    for name in ENTRANCES:
        dst=safe_path(backup,name);dst.parent.mkdir(parents=True,exist_ok=True)
        shutil.copyfile(safe_path(PUBLIC,name),dst)
        if file_pin(dst)!=manifest['replaced_navigation'][name]['before']:raise ValueError('Wrong backup')
    for name in NAMESPACES:
        dest=safe_path(PUBLIC,name);dest.parent.mkdir(parents=True,exist_ok=True)
        shutil.copytree(safe_path(payload,name),dest)
    for name in set(files)-set(ENTRANCES):
        if file_pin(safe_path(PUBLIC,name))!=files[name]:raise ValueError('New files differ')
    for name in reversed(ENTRANCES):
        dest=safe_path(PUBLIC,name)
        if file_pin(dest)!=manifest['replaced_navigation'][name]['before']:raise ValueError('Concurrent entrance change')
        pending=dest.with_name('.sqrt2-20261011-index.pending')
        with pending.open('xb') as stream:
            stream.write(safe_path(payload,name).read_bytes());stream.flush();os.fsync(stream.fileno())
        if file_pin(pending)!=files[name]:raise ValueError('Pending bytes differ')
        os.replace(pending,dest)
    current={**previous,**files}
    for name,expected in current.items():
        if file_pin(safe_path(PUBLIC,name))!=expected:raise ValueError('Post-activation mismatch: '+name)
    receipt=dict(status='passed',schema='sqrt2-faculty-checkpoint-activation-v1',
        manifest=pin(raw),payload_files=len(files),registered_public_files_verified=len(current),
        preserved_parent_files=len(previous)-3,rollback_directory=str(backup),new_library_admissions=0)
    with (private/'activation.json').open('xb') as stream:stream.write(encode(receipt))
    signal.alarm(0);return receipt


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--private',required=True,type=Path);parser.add_argument('--manifest-sha256',required=True)
    args=parser.parse_args();print(encode(activate(args.private,args.manifest_sha256)).decode())
