#!/usr/bin/env python3
"""Static link closure and exact public HTTPS bytes for the reviewed payload."""
import argparse
from concurrent.futures import ThreadPoolExecutor
from html.parser import HTMLParser
import json
from pathlib import Path
import time
from urllib.parse import urljoin,urlparse,unquote
from stage_sqrt2_power_research import ROOT,encode,inventory,pin,safe_path
from publish_sqrt2_power_checkpoint import RELEASE,NAMESPACE


class Links(HTMLParser):
    def __init__(self):super().__init__();self.urls=[]
    def handle_starttag(self,tag,attrs):
        self.urls.extend(v for k,v in attrs if k in {'href','src'} and v)


def verify(stage, *, public=False):
    raw=safe_path(stage,RELEASE).read_bytes();manifest=json.loads(raw)
    files={**manifest['files'],RELEASE:pin(raw)};inventory(stage,files)
    require=lambda condition,message: None if condition else (_ for _ in ()).throw(ValueError(message))
    require(manifest['new_library_admissions']==0 and manifest['published_supporting_statements']==245,'Wrong scope')
    old=ROOT/'_deploy/proofs-sqrt2-research-20261001';base=ROOT/'_deploy/proofs-v35'
    checked=0
    def link(source,url):
        nonlocal checked
        full=urlparse(urljoin('https://proof.invalid/proofs/'+source,url))
        if full.netloc!='proof.invalid' or not full.path.startswith('/proofs/'):return
        name=unquote(full.path.removeprefix('/proofs/'))
        if not name or name.endswith('/'):name+='index.html'
        found=any(safe_path(root,name).is_file() for root in (stage,old,base))
        require(found,'Broken local link: '+source+' -> '+name);checked+=1
    for name in files:
        if name.endswith('.html'):
            parser=Links();parser.feed(safe_path(stage,name).read_text())
            for url in parser.urls:link(name,url)
    graph=json.loads(safe_path(stage,NAMESPACE+'/api/notation-graph.json').read_bytes())
    ids={n['id'] for n in graph['nodes']}
    require(len(ids)==len(graph['nodes']),'Duplicate graph IDs')
    require(graph['theorem_count']==245 and graph['proof_edge_count']==0,'Notation graph claims proof edges')
    for node in graph['nodes']:link(NAMESPACE+'/definition-map.html',node['href'])
    for edge in graph['edges']:
        require(edge['source'] in ids and edge['target'] in ids,'Dangling graph edge')
        require(edge['kind'] in {'uses_definition','definition_uses_definition'},'Invented proof edge')
    result=dict(schema='sqrt2-checkpoint-delivery-validation-v1',status='passed',
        manifest_sha256=pin(raw)['sha256'],files=len(files),local_links_checked=checked,
        graph_nodes=len(ids),notation_edges=len(graph['edges']),public_https_checked=False,
        connected_browser_visual_qa=False,new_library_admissions=0)
    if public:
        from verify_sqrt2_power_publication import fetch_system_curl
        started=time.monotonic();deadline=started+300
        with ThreadPoolExecutor(max_workers=4) as pool:
            rows=list(pool.map(lambda item:fetch_system_curl(item[0],item[1],deadline),files.items()))
        result.update(public_https_checked=True,https=rows,https_wall_seconds=time.monotonic()-started,
            status='passed' if all(r['passed'] for r in rows) else 'failed')
    return result


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--stage',required=True,type=Path)
    p.add_argument('--public',action='store_true');p.add_argument('--output',required=True,type=Path)
    args=p.parse_args();r=verify(args.stage,public=args.public)
    with args.output.open('xb') as stream:stream.write(encode(r))
    print(encode({k:v for k,v in r.items() if k!='https'}).decode())
    raise SystemExit(r['status']!='passed')
