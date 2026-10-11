#!/usr/bin/env python3
"""Versioned research delivery, separate from Alpha admission.

Discovery only proposes a frozen index. Builds consume its explicitly pinned
HA/Lean pairs, authenticate complete archived sources, and display actual
certificates. No directory scan during build, proof producer, or kernel change.
The original October 1 release and its generator remain immutable.
"""
from __future__ import annotations
import argparse
import ast
from collections import defaultdict
import gzip
from hashlib import sha256
from html import escape
import importlib
import io
import json
from pathlib import Path
import re

from stage_sqrt2_power_research import ROOT, encode, pin, safe_path, inventory

OBS = ROOT / 'research/arithmetic-library/sqrt2-power/observations'
INDEX = OBS / 'publication-20261011-index.json'
INDEX_SHA256 = 'f66349af702f142fa1942ebfde2995ca941671086e2300ff81fd46a44fa47b32'
OUTPUT = ROOT / 'book/_static/constructive-sqrt2-power-checkpoint-20261011'
NAMESPACE = 'sqrt2-power/checkpoints/2026-10-11'
RELEASE = 'research-releases/sqrt2-power-2026-10-11/manifest.json'
OLD_RELEASE = 'research-releases/sqrt2-power-2026-10-01/manifest.json'
OLD_SHA = 'd724b221ed1913924ed51ca444b0874b6cebd5fe00c3aeabcc1c6cf7a9a0d802'
REVISION = sha256((ROOT/'artifacts/peano-library/alpha/catalog-v35.json').read_bytes()).hexdigest()[:12]
LEGACY_LEAN_ROWS=frozenset(('P04-soundness','P08-eprover','P08-vampire','P10',
                          'RF001','RF002','RF004','RF005','RF006'))
_VERIFIED_SNAPSHOTS=set()


def require(ok, message):
    if not ok:
        raise ValueError(message)


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':')).encode()


def proposed_index():
    """One-time discovery; immutable explicit output must be reviewed."""
    has, leans = defaultdict(list), defaultdict(list)
    for path in sorted(OBS.glob('*/report.json')):
        raw = path.read_bytes(); report = json.loads(raw)
        item = dict(path=str(path.relative_to(ROOT)), **pin(raw))
        if report.get('status') == 'fresh_ordinary_HA_checked':
            has[report['case']].append(item)
        if report.get('status') == 'fresh_lean_checked':
            for check in report['checks']:
                if check.get('independent_lean_checked') is True:
                    leans[(check['case'], check['report_sha256'])].append(item)
    rows = []
    for case, candidates in sorted(has.items()):
        matched = [(h, l) for h in candidates for l in leans[(case, h['sha256'])]]
        require(bool(matched), 'No exact Lean match: '+case)
        # Prefer the canonical shared-wave receipt, then the latest accepted
        # version. Every choice is subsequently literal, pinned index data.
        h, l = sorted(matched, key=lambda x: ('/shared-wave-' in x[0]['path'], x[0]['path'], x[1]['path']))[-1]
        r = json.loads((ROOT/h['path']).read_bytes())
        rows.append(dict(case=case, ha=h, lean=l,
            target_ast_sha256=r['results']['fresh_replay']['target_ast_sha256'],
            bundle_sha256=r['results']['fresh_replay']['bundle_sha256']))
    require(len(rows) == 246 and len({r['target_ast_sha256'] for r in rows}) == 245,
            'Expected 246 observations / 245 distinct statements')
    return dict(schema='sqrt2-research-checkpoint-index-v1', date='2026-10-11',
        authority='historical_evidence_not_admission', unique_statements=245,
        IR_parents_closed=0, library_admissions=0, rows=rows)


def pinned(item):
    raw = safe_path(ROOT, item['path']).read_bytes()
    require(pin(raw) == {k:item[k] for k in ('bytes','sha256')}, 'Changed indexed bytes: '+item['path'])
    return raw, json.loads(raw)


def load_index():
    raw=INDEX.read_bytes()
    require(sha256(raw).hexdigest()==INDEX_SHA256, 'Frozen index digest changed')
    index = json.loads(raw)
    require(index['schema']=='sqrt2-research-checkpoint-index-v1'
        and index['library_admissions']==index['IR_parents_closed']==0
        and len(index['rows'])==246 and len({r['case'] for r in index['rows']})==246
        and len({r['target_ast_sha256'] for r in index['rows']})==245,
        'Unexpected release inventory')
    return index


def authenticated_bundle(folder):
    """Same inert bindings as exact_bundle, with content-keyed snapshot reuse.

    Every compressed file is read anew; cached positive decompression checks
    are keyed by its SHA-256 AND the exact expected original length/hash.
    No proof acceptance, file path or failed validation is cached.
    """
    from check_sqrt2_power_fresh_lean import read_member
    from run_sqrt2_power_wave import SCHEMA,target_for,formula_sha256
    from sqrt2_power_wave_results import _read_file
    raw=_read_file(folder,'report.json');report=json.loads(raw)
    require(report.get('schema')==SCHEMA and report.get('status')=='fresh_ordinary_HA_checked'
        and report.get('IR_parents_closed')==report.get('library_admissions')==0,'Not checked research evidence')
    producer=read_member(folder,'generation',report);replay=read_member(folder,'fresh_replay',report)
    target_hash=formula_sha256(target_for(report['case']))
    for value in (producer,replay):
        require(value['schema']==SCHEMA and value['case']==report['case']
            and value['source_pins']==report['source_pins'] and value['IR_parents_closed']==0
            and value['target_ast_sha256']==target_hash,'Historical source/case/target mismatch')
    require(set(report['source_snapshots'])==set(report['source_pins']),'Missing source snapshots')
    for name,expected in report['source_pins'].items():
        path='sources/'+name+'.gz'
        require(report['source_snapshots'][name]==path and 0<expected['bytes']<=16*1024**2,'Wrong snapshot identity')
        compressed=_read_file(folder,path)
        key=(sha256(compressed).hexdigest(),expected['bytes'],expected['sha256'])
        if key not in _VERIFIED_SNAPSHOTS:
            with gzip.GzipFile(fileobj=io.BytesIO(compressed)) as stream:original=stream.read(expected['bytes']+1)
            require(pin(original)==expected,'Changed archived source')
            if len(_VERIFIED_SNAPSHOTS)<4096:_VERIFIED_SNAPSHOTS.add(key)
    payload=producer['bundle'].encode();digest=sha256(payload).hexdigest();tree=json.loads(payload)
    require(len(payload)<=8*1024**2 and producer['bundle_sha256']==replay['bundle_sha256']==digest
        and replay['status']=='fresh_ordinary_HA_checked' and tree[0]=='peano-lab-bundle-v1'
        and len(tree)==4 and len(tree[3])==replay['local_nodes']
        and sha256(canonical(tree[2])).hexdigest()==target_hash,'Canonical bundle binding changed')
    return payload,dict(case=report['case'],original_observation=str(folder.relative_to(ROOT)),
        report_sha256=sha256(raw).hexdigest(),bundle_sha256=digest,bundle_bytes=len(payload),
        nodes=replay['local_nodes'],root=tree[1],target_ast_sha256=target_hash)


def validate_pair(row):
    """Authenticate historical checks, never confer theorem-use authority."""
    from check_sqrt2_power_fresh_lean import MODULES, AUDIT_OUTPUT
    from sqrt2_power_automation_baseline import runtime
    from run_sqrt2_power_pilot import successful
    ha_raw, ha = pinned(row['ha']); lean_raw, lean = pinned(row['lean'])
    folder = (ROOT/row['ha']['path']).parent
    payload, binding = authenticated_bundle(folder)
    require(all(binding[k]==row[k] for k in ('case','target_ast_sha256','bundle_sha256')), 'Case binding changed')
    require(lean['status']=='fresh_lean_checked' and tuple(r['module'] for r in lean['compilation'])==MODULES,
            'Incomplete independent compilation')
    require(all(successful(r['process']) for r in lean['compilation']), 'Failed Lean compilation')
    checks = [r for r in lean['checks'] if r['case']==row['case'] and r['report_sha256']==binding['report_sha256']]
    require(len(checks)==1 and checks[0]['independent_lean_checked'] is True, 'Missing exact Lean check')
    check = checks[0]
    require(all(check[k]==binding[k] for k in ('bundle_sha256','target_ast_sha256','nodes')), 'Lean checked different bytes')
    if 'root' in check:
        require(check['root']==binding['root'], 'Lean root changed')
    else:
        require(row['case'] in LEGACY_LEAN_ROWS, 'Unregistered legacy Lean row')
    expected_stdout='ACCEPT\t'+check['process']['command'][-1]+f"\tnodes={binding['nodes']}\troot={binding['root']}\n"
    require(successful(check['process']) and check['process']['stdout']==expected_stdout, 'Lean acceptance missing')
    if 'axiom_audit' in lean:
        require(successful(lean['axiom_audit']) and lean['axiom_audit']['stdout']==AUDIT_OUTPUT, 'Axiom audit changed')
    for control in lean.get('negative_controls', []):
        require(control['rejected'] is True, 'Failed negative control')
    runtime_module = runtime()
    generation = None
    for phase in ('generation','fresh_replay'):
        saved = ha['process_records'][phase]
        raw = gzip.decompress((folder/saved['path']).read_bytes())
        require(sha256(raw).hexdigest()==saved['raw_sha256'], 'Changed HA process')
        process = json.loads(raw)
        if phase=='generation':
            # External hint inputs in the historical E/V cases remain bound
            # by their archived report; they never supply proof authority.
            original_input = b''
            if row['case'].startswith('P08-'):
                original_input = gzip.decompress((folder/'live-solver-input-and-observation.json.gz').read_bytes())
        else:
            original_input = canonical(generation)
        runtime_module.validate_process_record(process, command=tuple(process['command']),
            limits=runtime_module.ProcessLimits(**process['limits']), input_bytes=original_input)
        require(successful(process), 'Failed historical HA process')
        value = json.loads(process['stdout'])
        if phase=='generation': generation=value
        else:
            require(all(value[k] is True for k in ('original_target_checked','empty_context','false_target_rejected','forged_body_rejected')),
                    'Missing ordinary-kernel controls')
    return payload, binding, ha_raw, lean_raw, generation['diagnostics']


def case_modules():
    source = ast.parse((ROOT/'scripts/run_sqrt2_power_wave.py').read_bytes())
    function = next(n for n in source.body if isinstance(n, ast.FunctionDef) and n.name=='target_for')
    result = {}
    for node in ast.walk(function):
        if not isinstance(node, ast.If) or not isinstance(node.test, ast.Compare): continue
        test=node.test
        if len(test.comparators)!=1 or not isinstance(test.comparators[0],ast.Constant): continue
        case=test.comparators[0].value
        imports=[n.module for n in node.body if isinstance(n,ast.ImportFrom) and n.module.startswith('sqrt2_power_')]
        if imports: result[case]=imports[0]
    return result


def notation(case, diagnostics, target, modules):
    from peano_lab.kernel.formulas import pretty_formula
    from sqrt2_power_definitions import parse_named
    from peano_lab.library.proof_bundle import encode_formula
    module = importlib.import_module(modules[case]) if case in modules else None
    registry = None
    for name in ('definition_registry','convolution_definitions'):
        function = getattr(module,name,None)
        if callable(function): registry=function(); break
    source=diagnostics.get('source')
    if registry is None or not isinstance(source,str):
        return pretty_formula(target,[]), {}, []
    require(parse_named(source,registry=registry)==target, 'Named statement differs: '+case)
    defs={};used=[]
    for name,spec in registry.items():
        defs[spec.stable_id]=dict(id=spec.stable_id,name=name,parameters=list(spec.parameters),
            source=spec.template_source,ast=encode_formula(spec.template_formula),
            dependencies=[registry[d].stable_id for d in spec.conceptual_dependencies])
        if re.search(r'\b'+re.escape(name)+r'\s*\(', source):used.append(spec.stable_id)
    return source,defs,used


def shell(title, content, *, depth=0):
    p='../'*depth; home='/proofs/sqrt2-power/'
    return f'''<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"><title>{escape(title)} — irrationality research</title><link rel="stylesheet" href="/proofs/assets/proofs.css?v={REVISION}"><link rel="stylesheet" href="{home}assets/campaign-plan.css?v={REVISION}"></head><body class="family-page sqrt2-power-page"><header class="family-hero"><div class="shell"><nav class="crumbs"><a href="/proofs/">Proof library</a><span>/</span><a href="{home}">Irrationality campaign</a><span>/</span><a href="{p}index.html">11 October checkpoint</a><span>/</span><a href="{home}grand-campaign/index.html?view=family&amp;focus=F13">Grand campaign</a></nav><p class="eyebrow">HA + independent Lean evidence · Research, not Alpha admission</p><h1>{escape(title)}</h1><p class="lede">Full irrationality (IR072/G121) remains open. Stable: 432. Alpha v35: 4,318. This checkpoint changes neither catalogue.</p></div></header><main class="shell family-main">{content}</main></body></html>'''.encode()


def notation_graph(rows,definitions):
    """Exact notation arrows only; no containment link becomes a proof edge."""
    unique={}
    for row in rows:unique.setdefault(row['target_ast_sha256'],row)
    nodes=[dict(id=r['case'],tag=r['case'],name=r['title'],kind='theorem',layer=0,
        scope='research',status='HA/Lean checked research',summary=r['coverage'].replace('_',' '),
        alpha_checked_use=False,stable_member=False,href='checked/'+r['case']+'.html') for r in unique.values()]
    depths={}
    def depth(key,visiting=()):
        require(key not in visiting,'Cyclic definition graph')
        if key not in depths:depths[key]=1+max((depth(d,(*visiting,key)) for d in definitions[key]['dependencies']),default=-1)
        return depths[key]
    for key,d in definitions.items():
        nodes.append(dict(id=key,tag=key,name=d['name'],kind='definition',layer=depth(key),
            summary='Conservative HA abbreviation; not an axiom.',href='definition/'+key+'.html',
            parameters=d['parameters']))
    edges=[]
    for r in unique.values():
        for d in r['uses_definitions']:
            count=len(re.findall(r'\b'+re.escape(definitions[d]['name'])+r'\s*\(',r['statement']))
            edges.append(dict(source=r['case'],target=d,kind='uses_definition',
                occurrence_count=count,statement_occurrences=count,local_proposition_occurrences=0))
    edges += [dict(source=k,target=d,kind='definition_uses_definition') for k,row in definitions.items() for d in row['dependencies']]
    notation={n['id']:dict(uses=[],used_by=[]) for n in nodes}
    for e in edges:
        notation[e['source']]['uses'].append(e['target']);notation[e['target']]['used_by'].append(e['source'])
    proof={r['case']:dict(dependencies=[],dependents=[],ancestors=[],descendants=[],
        critical_root_path=[r['case']],foundation_path=[r['case']],shortest_root_path=[r['case']],root_path_count=1) for r in unique.values()}
    data=dict(schema='peano-lab-pa-defined-graph-v1',nodes=nodes,edges=edges,
        theorem_count=len(unique),definition_count=len(definitions),proof_edge_count=0,
        definition_edge_count=sum(len(d['dependencies']) for d in definitions.values()),
        notation_edge_count=len(edges),theorem_definition_edge_count=sum(len(r['uses_definitions']) for r in unique.values()),
        definition_topological_order=sorted(definitions,key=lambda d:(depths[d],d)),
        definition_layer_count=1+max(depths.values(),default=-1),
        proof_layers=[dict(index=0,nodes=list(proof))],proof_foundations=list(proof),proof_terminals=list(proof),
        proof_adjacency=proof,notation_adjacency=notation,path_policy='proof_dependency_edges_only',
        graph_checked_use_count=0,graph_alpha_closed_count=0,graph_stable_closed_count=0,graph_newly_promoted_count=0,
        authority='notation_map_not_proof_dependency_map',alpha_edition_version='v35',alpha_edition_checked_use_count=4318)
    original=(ROOT/'book/_static/pa-proof-explorer/defined/graph.html').read_text()
    controls=original.split('<main class="pd-graph-page"',1)[1].split('</main>',1)[0]
    controls=('<main class="pd-graph-page"'+controls+'</main>').replace('value="PA00FW"','value="AP095"')
    inline=json.dumps(data,separators=(',',':'),ensure_ascii=False).replace('<','\\u003c')
    html=f'''<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Research notation DAG</title><link rel="stylesheet" href="/proofs/assets/defined-explorer.css?v={REVISION}"><script defer src="/proofs/assets/defined-explorer.js?v={REVISION}"></script></head><body class="pa-defined-proof-site" data-page="graph"><header class="pd-header"><nav><a href="index.html">245 checked statements</a><a href="definitions.html">Definition directory</a><a href="/proofs/sqrt2-power/map.html?target=IR072">Campaign plan</a></nav><p class="pd-kicker">Exact conservative notation · Research checkpoint</p><h1>Statements and their definitions</h1><p>This map contains notation-use and definition-expansion arrows only. It is not a proof-dependency map. Complete private proof DAGs are downloadable from every statement page. Alpha and Stable are unchanged.</p></header>{controls}<script id="pa-defined-graph-data">window.PA_DEFINED_GRAPH={inline};</script></body></html>'''.encode()
    return data,html


def build(output):
    """Sequential bounded records; never materialize every certificate together."""
    require(not output.exists(), 'New output directory required')
    index=load_index(); modules=case_modules(); rows=[]; definitions={}; row_targets={}
    files={}; output.mkdir(parents=True)
    def save(name,raw):
        path=safe_path(output,name);path.parent.mkdir(parents=True,exist_ok=True)
        with path.open('xb') as stream:stream.write(raw)
        files[name]=pin(raw)
    save('api/index.json',INDEX.read_bytes())
    for item in index['rows']:
        payload,binding,ha_raw,lean_raw,diagnostics=validate_pair(item)
        tree=json.loads(payload)
        from peano_lab.library.proof_bundle import decode_formula
        target=decode_formula(tree[2])
        named,defs,uses=notation(item['case'],diagnostics,target,modules)
        for key,value in defs.items():
            require(key not in definitions or definitions[key]==value, 'Definition identity collision: '+key)
            definitions[key]=value
        row=dict(binding,title=Path(item['ha']['path']).parent.name.removeprefix('shared-wave-').rsplit('-v',1)[0].replace('-',' '),
            statement=named,uses_definitions=uses,coverage=diagnostics.get('coverage','exact supporting statement'),
            internal_proof_nodes=tree[3][tree[1]][2],
            proof='evidence/'+item['case']+'-bundle.json.gz',ha='evidence/'+item['case']+'-HA.json.gz',
            lean='evidence/'+item['case']+'-Lean.json.gz',
            embedded_statement_hashes=sorted({sha256(canonical(n[1])).hexdigest() for i,n in enumerate(tree[3]) if i!=tree[1]}))
        rows.append(row);row_targets[item['target_ast_sha256']]=item['case']
        save(row['proof'],gzip.compress(payload,mtime=0))
        save(row['ha'],gzip.compress(ha_raw,mtime=0));save(row['lean'],gzip.compress(lean_raw,mtime=0))
        save('api/targets/'+item['case']+'.json',encode(tree[2]))
        print(item['case']+' authenticated',flush=True)
    # Named statements linked only when an exactly equal target is present in
    # the actual dependency-closed certificate. These are containment links,
    # explicitly NOT claimed to be direct proof edges.
    for row in rows:
        row['contains_checked_statements']=sorted({row_targets[h] for h in row.pop('embedded_statement_hashes') if h in row_targets and row_targets[h]!=row['case']})
        code=row['case']; used=' · '.join('<a href="../definition/'+d+'.html">'+d+' — '+escape(definitions[d]['name'])+'</a>' for d in row['uses_definitions']) or 'No displayed named abbreviation.'
        body='<section class="release-note"><h2>Exact named statement</h2><pre class="contract"><code>'+escape(row['statement'].replace(' -> ',' ->\n  '))+'</code></pre><p>'+used+'</p><p><a href="../api/targets/'+code+'.json">Fully expanded target AST</a></p></section>'
        body+='<section class="release-note"><h2>Complete certificate and independent checks</h2><p>'+str(row['nodes'])+' actual local proof nodes. Each node carries its complete ordinary HA proof body.</p><p>'+ ' · '.join('<a href="../'+row[k]+'">'+title+'</a>' for k,title in [('proof','Full canonical proof bundle'),('ha','Original HA receipt'),('lean','Independent Lean receipt')])+'</p><p class="contract">Target SHA-256: '+row['target_ast_sha256']+'<br>Bundle SHA-256: '+row['bundle_sha256']+'</p></section>'
        body+='<section class="release-note"><h2>Checked statement containment</h2><p>These exact targets occur inside this certificate. These links summarize containment, not direct dependency arrows; the downloadable bundle records every private lemma and ordered edge.</p><p>'+ ' · '.join('<a href="'+c+'.html">'+c+'</a>' for c in row['contains_checked_statements'])+'</p><h2>Scope</h2><p>'+escape(row['coverage'].replace('_',' '))+'</p><p>None of these finite arithmetic statements closes an IR campaign parent. The analytic identification, interpolation and final positive irrationality certificate remain open.</p></section>'
        save('checked/'+code+'.html',shell(code+' — '+row['title'],body,depth=1))
    for key,row in sorted(definitions.items()):
        users=[r['case'] for r in rows if key in r['uses_definitions']]
        body='<section class="release-note"><h2>Conservative definition</h2><p>Parameters: '+escape(', '.join(row['parameters']))+'</p><pre class="contract"><code>'+escape(row['source'])+'</code></pre><h3>Definition prerequisites</h3><p>'+ ' · '.join('<a href="'+d+'.html">'+d+'</a>' for d in row['dependencies'])+'</p><h3>Theorem uses (notation, not proof premises)</h3><p>'+ ' · '.join('<a href="../checked/'+c+'.html">'+c+'</a>' for c in users)+'</p></section>'
        save('definition/'+key+'.html',shell(key+' — '+row['name'],body,depth=1))
    summary=dict(schema='sqrt2-research-checkpoint-corpus-v1',authority='historical_evidence_not_admission',
        unique_statements=245,observation_count=246,library_admissions=0,IR_parents_closed=0,
        rows=rows,definitions=list(definitions.values()))
    save('api/corpus.json',encode(summary))
    graph,graph_html=notation_graph(rows,definitions)
    save('api/notation-graph.json',encode(graph));save('definition-map.html',graph_html)
    table=''.join('<tr><th><a href="checked/'+r['case']+'.html">'+r['case']+'</a></th><td>'+escape(r['title'])+'</td><td>'+str(r['nodes'])+'</td><td>HA + Lean</td></tr>' for r in rows)
    cards='''<section class="view-grid"><article class="view-card featured"><p class="card-kicker">Latest result</p><h2>Requested half-root error</h2><p>AP095 proves the finite error at most 2⁻ⁿ for the unchanged n+8 sample program.</p><a href="checked/AP095.html">Read AP095 →</a></article><article class="view-card"><p class="card-kicker">Definitions first</p><h2>Conservative notation</h2><p>Exact expanded definitions and their prerequisite/use links. No new kernel axioms.</p><a href="definitions.html">Browse definitions →</a></article><article class="view-card"><p class="card-kicker">Bigger picture</p><h2>Irrationality remains open</h2><p>245 distinct supporting statements, not 245 closed campaign goals. Transcendence follows irrationality.</p><a href="/proofs/sqrt2-power/map.html?target=IR072&amp;view=prerequisites">Open the campaign DAG →</a></article></section>'''
    body=cards+'<section class="release-note"><h2>All checked supporting results</h2><p>246 HA/Lean observations represent 245 distinct statements; the E and Vampire P08 demonstrations share one target. The original 33-statement release remains available unchanged.</p><div class="pilot-results-scroll"><table class="pilot-results-table"><thead><tr><th>Case</th><th>Statement</th><th>Local proof nodes</th><th>Evidence</th></tr></thead><tbody>'+table+'</tbody></table></div></section><section class="release-note"><h2>Reproducibility and honest status</h2><p><a href="api/corpus.json">Full structured inventory</a> · <a href="api/index.json">Pinned source evidence index</a> · <a href="api/manifest.json">Delivery hashes</a> · <a href="/proofs/sqrt2-power/wave-results.html">Historical 33-statement checkpoint</a>.</p><p>HA and Lean receipts are observations, not checked-use admission tokens. Kernel bodies remain the proof authority. Agent engineering costs are not represented as zero, and external solver hits are not asserted to be translated proofs.</p></section>'
    save('index.html',shell('245 checked supporting statements',body))
    save('definitions.html',shell('Conservative definition directory','<section class="release-note"><p><a href="definition-map.html?target=AP095&amp;view=neighborhood&amp;definitions=selected&amp;edges=all">Interactive definition DAG</a>. Definition dependencies and theorem uses are separate from proof premises.</p><ul>'+''.join('<li><a href="definition/'+k+'.html">'+k+' — '+escape(d['name'])+'</a></li>' for k,d in sorted(definitions.items()))+'</ul></section>'))
    save('api/manifest.json',encode(dict(schema='sqrt2-research-checkpoint-build-v1',authority='research_publication_not_library_admission',new_library_admissions=0,files=files.copy())))
    print(json.dumps(dict(status='built',files=len(files),definitions=len(definitions),unique_statements=245)))


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    group=parser.add_mutually_exclusive_group(required=True)
    group.add_argument('--propose-index',action='store_true')
    group.add_argument('--build',type=Path)
    args=parser.parse_args()
    if args.propose_index:
        require(not INDEX.exists(),'Frozen index already exists')
        with INDEX.open('xb') as stream:stream.write(encode(proposed_index()))
        print(json.dumps(pin(INDEX.read_bytes())))
    else: build(args.build)
