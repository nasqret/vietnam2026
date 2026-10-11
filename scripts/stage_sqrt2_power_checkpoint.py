#!/usr/bin/env python3
"""Stage the additive October 11 checkpoint over both sealed predecessors."""
import argparse
import json
from pathlib import Path
from stage_sqrt2_power_research import (
    ROOT, PARENT, PARENT_MANIFEST, PARENT_SHA256,
    authenticated_manifest, encode, file_pin, inventory, pin, safe_path,
)
from publish_sqrt2_power_checkpoint import NAMESPACE, RELEASE, OLD_RELEASE, OLD_SHA, INDEX_SHA256

OLD = ROOT/'_deploy/proofs-sqrt2-research-20261001'
ENTRANCES=('index.html','grand-campaign/index.html','sqrt2-power/index.html')


def stage(site, output):
    if output.exists(): raise ValueError('New stage required')
    _,parent=authenticated_manifest(PARENT,PARENT_MANIFEST,PARENT_SHA256,'current_files')
    old,old_files=authenticated_manifest(OLD,OLD_RELEASE,OLD_SHA,'files')
    before={**parent,**old_files}
    raw=safe_path(site,'api/manifest.json').read_bytes();site_manifest=json.loads(raw)
    expected={**site_manifest['files'],'api/manifest.json':pin(raw)}
    inventory(site,expected)
    if (site_manifest['new_library_admissions']!=0
        or pin(safe_path(site,'api/index.json').read_bytes())['sha256']!=INDEX_SHA256):
        raise ValueError('Unexpected evidence boundary')
    payload={NAMESPACE+'/'+name:safe_path(site,name).read_bytes() for name in expected}
    for name in ENTRANCES:
        data=safe_path(OLD,name).read_bytes()
        if pin(data)!=before[name]:raise ValueError('Changed previous entrance')
        if name=='index.html':
            data=data.replace(b'1 October 2026',b'11 October 2026').replace(b'33 distinct HA/Lean',b'245 distinct HA/Lean')
            data=data.replace(b'href="sqrt2-power/"',b'href="sqrt2-power/checkpoints/2026-10-11/"')
            data=data.replace(b'href="sqrt2-power/arithmetic-frontier.html">Checked arithmetic DAG',
                              b'href="sqrt2-power/checkpoints/2026-10-11/definition-map.html">Definition-use DAG')
            data=data.replace(b'href="sqrt2-power/quadratic-trace-definitions.html">Finite-product definitions',
                              b'href="sqrt2-power/checkpoints/2026-10-11/definitions.html">Conservative definitions')
            data=data.replace(OLD_RELEASE.encode(),RELEASE.encode())
        elif name=='grand-campaign/index.html':
            data=data.replace(b'33 checked supporting statements and their arithmetic DAG',b'245 checked supporting statements and exact certificates')
            data=data.replace(b'../sqrt2-power/arithmetic-frontier.html',b'../sqrt2-power/checkpoints/2026-10-11/index.html')
        else:
            marker=b'<main class="shell family-main">'
            if data.count(marker)!=1:raise ValueError('Changed campaign entrance structure')
            notice=b'''<section class="release-note" id="checkpoint-20261011"><h2>Latest checked research: 11 October 2026</h2><p><a href="checkpoints/2026-10-11/index.html">245 distinct HA/Lean-checked supporting statements</a> through <a href="checkpoints/2026-10-11/checked/AP095.html">AP095: requested half-root error</a>. <a href="checkpoints/2026-10-11/definitions.html">Browse their conservative definitions</a>.</p><p>Full irrationality remains open. Alpha v35 and Stable are unchanged. The earlier 33-statement checkpoint below is retained as historical evidence.</p></section>'''
            data=data.replace(marker,marker+notice)
        if data==safe_path(OLD,name).read_bytes():raise ValueError('Entrance was not updated')
        payload[name]=data
    manifest=dict(schema='sqrt2-power-research-delivery-v2',
        authority='research_publication_not_library_admission',new_library_admissions=0,
        published_supporting_statements=245,IR072_proved=False,TR006_proved=False,
        current_alpha_version='v35',current_alpha_checked_use_count=4318,stable_count=432,
        parent_manifests=[dict(path=PARENT_MANIFEST,sha256=PARENT_SHA256,field='current_files'),
                          dict(path=OLD_RELEASE,sha256=OLD_SHA,field='files')],
        namespaces=[NAMESPACE,str(Path(RELEASE).parent)],
        replaced_navigation={name:dict(before=before[name],after=pin(payload[name])) for name in ENTRANCES},
        files={name:pin(raw) for name,raw in sorted(payload.items())},payload_file_count=len(payload)+1)
    payload[RELEASE]=encode(manifest)
    for name,raw in payload.items():
        path=safe_path(output,name);path.parent.mkdir(parents=True,exist_ok=True)
        with path.open('xb') as stream:stream.write(raw)
    inventory(output,{name:pin(raw) for name,raw in payload.items()})
    return dict(status='staged',files=len(payload),manifest_sha256=pin(payload[RELEASE])['sha256'])


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--site',required=True,type=Path);p.add_argument('--output',required=True,type=Path)
    args=p.parse_args();print(encode(stage(args.site,args.output)).decode())
