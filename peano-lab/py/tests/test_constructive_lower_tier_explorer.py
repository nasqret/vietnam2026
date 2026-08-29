"""Actual lower-tier proof evidence, canonical QR structure and live JS contracts.

Positive rendering invokes original HA and the pinned compiled Lean verifier.
The browser is unavailable in this environment; actual canonical JavaScript is
therefore exercised in the established hostile-SVG DOM harness, not advertised
as visual browser QA. No production proof checker is stubbed to accept.
"""

from __future__ import annotations

import ast
from collections import Counter
from hashlib import sha256
from html.parser import HTMLParser
import json
from pathlib import Path
import posixpath
import subprocess
import sys
from types import SimpleNamespace
from urllib.parse import parse_qs, unquote, urlsplit

import pytest


ROOT=Path(__file__).resolve().parents[3]
sys.path.insert(0,str(ROOT/'scripts'))
import build_constructive_lower_tier_explorer as builder
import constructive_lower_tier_checkpoints as checkpoints
import constructive_bottom_layer_checkpoints as previous
from constructive_lower_tier_definitions import ALL_CONSTRUCTIVE_DEFINITIONS_BY_NAME as DEFINITIONS
from constructive_formula_compactor import _LocalDefinedParser
from peano_lab.kernel.formulas import parse_formula_with_names


SLUGS=('divisor-sums','signed-weighted-sums','prime-field-polynomials')
EXPECTED_COUNTS={'divisor-sums':37,'signed-weighted-sums':40,'prime-field-polynomials':49}
EXPECTED_PREFIXES={'divisor-sums':'DV','signed-weighted-sums':'WS','prime-field-polynomials':'PP'}


def _drivers():
    """Reuse unchanged actual-asset drivers without importing old editions."""
    path=ROOT/'peano-lab/py/tests/test_constructive_bottom_layer_explorer.py'
    names={
        'Document','_strict_json','_graph_runtime','_landing_structure',
        'test_every_theorem_statement_script_and_all_local_propositions_are_exact',
        'test_definition_identity_exactness_and_acyclic_three_kind_dag',
        'test_actual_canonical_dashboard_and_local_addon_combine_all_three_filters',
        'test_actual_defined_reader_highlights_initial_fragment_and_focuses_hash_changes',
    }
    selected=[node for node in ast.parse(path.read_text()).body if isinstance(node,(ast.FunctionDef,ast.ClassDef)) and node.name in names]
    assert {node.name for node in selected}==names
    for node in selected:node.decorator_list=[]
    namespace={
        'ROOT':ROOT,'builder':builder.model,'HTMLParser':HTMLParser,'json':json,
        'ast':ast,'Path':Path,'subprocess':subprocess,'SimpleNamespace':SimpleNamespace,
        'sha256':sha256,'DEFINITIONS':DEFINITIONS,'parse_formula_with_names':parse_formula_with_names,
        '_LocalDefinedParser':_LocalDefinedParser,
    }
    exec(compile(ast.Module(body=selected,type_ignores=[]),str(path),'exec'),namespace)
    return namespace


@pytest.fixture(scope='module')
def drivers():
    return _drivers()


@pytest.fixture(scope='module')
def families():
    result=builder.families()
    assert tuple(row.slug for row in result)==SLUGS
    assert {row.slug:row.prefix for row in result}==EXPECTED_PREFIXES
    return {row.slug:row for row in result}


@pytest.fixture(scope='module')
def files():
    immutable=(
        ROOT/'artifacts/peano-library/alpha/catalog-v30.json',
        ROOT/'book/_static/constructive-bottom-layer-explorer/manifest.json',
        ROOT/'book/_static/constructive-bottom-layer-publication/manifest.json',
        ROOT/'book/_static/constructive-gaussian-campaign/campaign.json',
        ROOT/'book/_static/constructive-gaussian-campaign/definitions.json',
        ROOT/'book/_static/constructive-gaussian-campaign/index.html',
    )
    before={path:sha256(path.read_bytes()).hexdigest() for path in immutable}
    # Real proof checks. No sidecar, class instance, or admission Boolean is a
    # substitute for the original complete HA check and actual Lean process.
    result=builder.build_files()
    assert {path:sha256(path.read_bytes()).hexdigest() for path in immutable}==before
    builder.model.write_or_check(result,output=builder.OUTPUT,check=True)
    return result


@pytest.fixture(scope='module')
def corpora(files):
    return {slug:json.loads(files[slug+'/api/corpus.json']) for slug in SLUGS}


def test_exact_inventory_and_separate_non_admitting_membership(files,corpora):
    inventory=json.loads(files['checkpoints.json'])
    expected=checkpoints.all_new_rows()
    assert inventory['schema']==builder.SCHEMA
    assert inventory['publication_scope']=='local-only-checkpoint'
    assert inventory['published'] is inventory['alpha_admission_performed'] is inventory['stable_admission_performed'] is False
    assert inventory['inherited_support_counted_as_new'] is False
    assert inventory['previous_research_theorems']==170
    assert inventory['parent']['alpha_version']=='v30'
    assert inventory['parent']['alpha_checked_use_count']==3222
    assert inventory['parent']['stable_count']==432
    assert inventory['parent']['catalog_sha256']=='ac7111ec14ff07bf899238ed465de337e6d76e9343384947022360dc7e65d9f7'
    assert inventory['navigation_revision']=='ac7111ec14ff'
    assert inventory['new_theorems']==sum(corpus['node_count'] for corpus in corpora.values())==len(expected)==126
    assert {slug:corpus['node_count'] for slug,corpus in corpora.items()}==EXPECTED_COUNTS
    assert Counter(row['name'] for corpus in corpora.values() for row in corpus['nodes'])==Counter(row.name for row in expected)
    assert inventory['statement_asts_distinct_from_all_3392_prior_and_each_other'] is True
    assert len({row.name for row in expected})==len(expected)


@pytest.mark.parametrize('slug',SLUGS)
def test_new_rows_never_launder_inherited_research_into_alpha(slug,files,corpora,families):
    corpus=corpora[slug]
    checkpoint=next(row for row in checkpoints.CHECKPOINTS if row.slug==slug)
    owned=checkpoints.load_rows(checkpoint)
    report=json.loads(files[slug+'/api/checkpoint.json'])
    assert report==corpus['checkpoint_report']
    assert report['new_theorem_count']==len(owned)==corpus['node_count']==corpus['new_theorem_count']
    assert report['membership']=='local_non_admitting_checkpoint'
    assert report['bundle']['original_ha_checked'] is report['bundle']['independent_lean_checked'] is True
    assert report['bundle']['sha256']==checkpoint.artifact_sha256
    assert len(files['checkpoints/'+Path(checkpoint.artifact).name])==checkpoint.artifact_bytes
    assert sha256(files['checkpoints/'+Path(checkpoint.artifact).name]).hexdigest()==checkpoint.artifact_sha256
    assert files['checkpoints/'+Path(checkpoint.artifact).name]==(ROOT/checkpoint.artifact).read_bytes()
    assert all(row['complete_ordinary_ha_checked'] is False for row in report['principal_roots'])
    assert {row['name'] for row in corpus['nodes']}=={row.name for row in owned}
    assert all(row['inventory_role']=='new_owned_theorem' for row in corpus['nodes'])
    for record in (corpus,*corpus['nodes']):
        assert builder.render._status(record)==builder.render.STATUS
        assert all(record[key] is False for key in builder.render.FORBIDDEN_ADMISSION_FIELDS)
        assert 'alpha_edition_version' not in record and 'alpha_first_enrolled_version' not in record
    assert corpus['alpha_enrolled_node_count']==corpus['alpha_checked_use_node_count']==corpus['stable_admitted_node_count']==0
    support=report['support']
    assert support['counted_as_new_owned_theorems'] is False
    assert (support['published_non_admitted_count']+support['current_cross_track_count']+
            support['alpha_v30_count']+len(owned)+1)==report['bundle']['nodes_including_packaging_root']
    by_name={row.name:row for row in (*builder.closure.parent_snapshot().specs,*builder.previous_rows(),*checkpoints.all_new_rows())}
    for external in corpus['external_dependencies']:
        name=external['name']
        assert external['counted_as_new_owned_theorem'] is False
        assert external['statement']==by_name[name].statement
        assert external['statement_sha256']==sha256(by_name[name].statement.encode()).hexdigest()
        admitted=external['inventory_role']=='inherited_alpha_v30'
        assert external['admitted_to_alpha'] is external['alpha_checked_use'] is external['enrolled_in_alpha'] is admitted
        if not admitted:
            assert external['parent_alpha_version'] is None
            expected_role=('inherited_published_non_admitted_checkpoint'
                           if name in support['published_non_admitted_theorems'] else 'new_cross_track_support')
            assert external['inventory_role']==expected_role
    assert corpus['root_names']==list(families[slug].roots)
    assert set(corpus['root_names'])<={row.name for row in owned}


@pytest.mark.parametrize('slug',SLUGS)
def test_every_statement_tactic_and_local_proposition_is_the_exact_owned_proof(slug,files,corpora,families,drivers):
    checkpoint=next(row for row in checkpoints.CHECKPOINTS if row.slug==slug)
    for row in checkpoints.load_rows(checkpoint):
        drivers['test_every_theorem_statement_script_and_all_local_propositions_are_exact'](families[slug],row,files,corpora)
    for pin in checkpoint.modules:
        assert files['sources/'+Path(pin.path).name]==previous._source_bytes(pin)
        assert sha256(files['sources/'+Path(pin.path).name]).hexdigest()==pin.sha256
    assert files['sources/'+Path(checkpoint.rfc).name]==(ROOT/checkpoint.rfc).read_bytes()


@pytest.mark.parametrize('slug',SLUGS)
def test_exact_conservative_definition_dag_and_proof_only_paths(slug,files,corpora,families,drivers):
    drivers['test_definition_identity_exactness_and_acyclic_three_kind_dag'](families[slug],corpora,files)
    graph=json.loads(files[slug+'/api/graph.json'])
    assert graph==json.loads(files[slug+'/explorer/defined/api/graph.json'])
    assert {row['name'] for row in graph['nodes'] if row['kind']=='theorem'}=={row['name'] for row in corpora[slug]['nodes']}
    assert graph['publication_scope']=='local-only-checkpoint'
    for row in graph['nodes']:
        if row['kind']=='theorem':
            assert row['local_checkpoint_verified'] is True
            assert all(row[key] is False for key in builder.render.FORBIDDEN_ADMISSION_FIELDS)


def test_weighted_graphs_use_the_actual_old_signed_definitions_and_new_exact_ids(corpora):
    definitions={row['name']:row for row in corpora['signed-weighted-sums']['definitions']}
    for name,identifier,parameters,parents in (
        ('ArithAdd','ND0266',('F','G','H','l'),('ArithTable','Lt','ArithAt','SignedAdd')),
        ('ArithMul','ND0267',('F','G','H','l'),('ArithTable','Lt','ArithAt','SignedMul')),
        ('ArithScale','ND0268',('a','F','G','l'),('ArithTable','Lt','ArithAt','SignedMul')),
        ('SignedWeightedSum','ND0272',('W','F','l','z'),('ArithMul','SignedPrefixSum')),
    ):
        row=definitions[name]
        assert row['id']==identifier
        assert row['parameters']==list(parameters)
        assert row['dependency_names']==list(parents)
    node=next(row for row in corpora['signed-weighted-sums']['nodes'] if row['name']=='signed_weighted_sum_add_linearity')
    assert 'ArithAdd(F,G,H,l)' in node['defined']['defined_statement']
    assert 'SignedWeightedSum(W,F,l,a)' in node['defined']['defined_statement']
    assert 'SignedAdd(a,b,c)' in node['defined']['defined_statement']


@pytest.mark.parametrize('slug',SLUGS)
def test_canonical_qr_landing_and_exact_defined_page_topology(slug,files,corpora,drivers):
    reference=ROOT/'book/_static/constructive-gaussian-factorization-explorer/gaussian-factorization/index.html'
    assert drivers['_landing_structure'](files[slug+'/index.html'])==drivers['_landing_structure'](reference.read_bytes())
    document=drivers['Document'](files[slug+'/index.html'])
    assert sum('view-card' in attrs.get('class','').split() for _,attrs in document.tags)==3
    assert any(attrs.get('name')=='robots' and attrs.get('content')=='noindex' for _,attrs in document.tags)
    assert not any(attrs.get('rel')=='canonical' for _,attrs in document.tags)
    for row in corpora[slug]['nodes']:
        for view in ('explorer/tag/','explorer/defined/tag/'):
            assert slug+'/'+view+row['id']+'.html' in files
    for row in corpora[slug]['definitions']:
        assert slug+'/explorer/defined/definition/'+row['id']+'.html' in files


def test_all_five_historical_assets_are_byte_identical(files):
    for name,expected in builder.ASSET_DIGESTS.items():
        assert files['assets/'+name]==builder.model.ASSET_SOURCES[name].read_bytes()
        assert sha256(files['assets/'+name]).hexdigest()==expected


def test_every_actual_link_and_fragment_resolves_across_new_old_and_atlas(files,drivers):
    Document=drivers['Document']
    documents={name:Document(payload) for name,payload in files.items() if name.endswith('.html')}
    previous_documents={}
    used_previous=used_cross=used_atlas=0
    for name,document in documents.items():
        assert len(document.ids)==len(set(document.ids)),name
        for tag,attrs in document.tags:
            for key in ('href','src'):
                if key not in attrs:continue
                url=urlsplit(attrs[key])
                assert not url.scheme and not url.netloc and not url.path.startswith('/'),(name,attrs[key])
                target=posixpath.normpath(posixpath.join(posixpath.dirname(name),unquote(url.path))) if url.path else name
                if url.path.endswith('/'):target=posixpath.normpath(target+'/index.html')
                if target.startswith('../'):
                    assert target=='../constructive-gaussian-campaign/index.html' or target.startswith('../constructive-bottom-layer-explorer/'),(name,attrs[key])
                    path=builder.OUTPUT/target
                    assert path.is_file(),(name,attrs[key])
                    if target.startswith('../constructive-bottom-layer-explorer/'):
                        used_previous+=1
                    else:used_atlas+=1
                    if url.fragment:
                        if target not in previous_documents:previous_documents[target]=Document(path.read_bytes())
                        assert unquote(url.fragment) in previous_documents[target].ids
                else:
                    assert target in files,(name,attrs[key],target)
                    if target.split('/',1)[0] in SLUGS and target.split('/',1)[0]!=name.split('/',1)[0]:used_cross+=1
                    if url.fragment:assert unquote(url.fragment) in documents[target].ids,(name,attrs[key])
                if url.path:
                    asset=Path(url.path).name
                    expected=builder.ASSET_DIGESTS[asset][:12] if tag in {'script','link'} and asset in builder.render.ASSET_DIGESTS else builder.HTML_REVISION
                    assert parse_qs(url.query).get('v')==[expected],(name,attrs[key])
    assert used_previous>0 and used_cross>0 and used_atlas>0


def test_every_inline_script_parses_and_graph_payload_matches_its_api(files,drivers):
    scripts=[]
    for name,payload in files.items():
        if not name.endswith('.html'):continue
        for attrs,source in drivers['Document'](payload).scripts:
            if attrs.get('type','').lower() in {'application/json','application/ld+json'}:
                drivers['_strict_json'](source)
            elif 'src' not in attrs:scripts.append({'name':name,'source':source})
            if attrs.get('id')=='pa-defined-graph-data':
                assert source.startswith('window.PA_DEFINED_GRAPH=') and source.endswith(';')
                graph=drivers['_strict_json'](source[len('window.PA_DEFINED_GRAPH='):-1])
                assert graph==drivers['_strict_json'](files[name.replace('graph.html','api/graph.json')])
    program='const vm=require("node:vm"),rows=JSON.parse(require("node:fs").readFileSync(0,"utf8"));rows.forEach(x=>new vm.Script(x.source,{filename:x.name}));process.stdout.write(String(rows.length));'
    result=subprocess.run(['node','-e',program],input=json.dumps(scripts),text=True,capture_output=True,check=True,timeout=20)
    assert int(result.stdout)==len(scripts)==11


@pytest.mark.parametrize('slug',SLUGS)
@pytest.mark.parametrize('focus_kind',('theorem','definition'))
def test_actual_canonical_mixed_graph_with_getter_only_svg_hrefs(slug,focus_kind,files,drivers):
    graph=json.loads(files[slug+'/api/graph.json'])
    target=graph['root_ids'][-1]
    focus=target if focus_kind=='theorem' else next(row['id'] for row in graph['nodes'] if row['kind']=='definition')
    actual=drivers['_graph_runtime'](graph,target,focus,complete_family=True,visible_definitions=True)
    assert actual['svgHrefIsGetterOnly'] is actual['allSvgHrefsAreGetterOnly'] is actual['viewportRendered'] is True
    assert actual['selectedNodeIds']==[focus]
    assert actual['sidebarHref']==next(row['href'] for row in graph['nodes'] if row['id']==focus)
    assert {row['id'] for row in graph['nodes'] if row['kind']=='theorem'}<=set(actual['renderedNodeIds'])


@pytest.mark.parametrize('slug',SLUGS)
@pytest.mark.parametrize('ready,canonical_first',(('loading',True),('complete',False)))
def test_actual_three_filters_and_hash_highlighting(slug,ready,canonical_first,files,corpora,families,drivers):
    drivers['test_actual_canonical_dashboard_and_local_addon_combine_all_three_filters'](families[slug],ready,canonical_first,files,corpora)
    drivers['test_actual_defined_reader_highlights_initial_fragment_and_focuses_hash_changes'](families[slug],files,corpora)


def test_actual_exact_graph_navigation_never_injects_a_missing_link(files,corpora,drivers):
    cases=[]
    for name,payload in files.items():
        if '/explorer/' not in name or '/defined/' in name or not name.endswith('.html'):continue
        document=drivers['Document'](payload)
        links=[attrs['href'] for tag,attrs in document.header_tags if tag=='a' and 'data-graph-navigation' in attrs]
        assert len(links)==1 and 'defined/graph.html' in links[0],name
        page=next(attrs['data-page'] for tag,attrs in document.tags if tag=='body')
        cases.append({'name':name,'page':page,'href':links[0]})
    source=builder.model.ASSET_SOURCES['exact-explorer.js'].read_text()
    start=source.index('  function initializeGraphNavigation()');end=source.index('\n  function ',start+1)
    program='''const vm=require("node:vm"),input=JSON.parse(require("node:fs").readFileSync(0,"utf8"));
input.cases.forEach(row=>{const anchor={getAttribute(){return row.href;}};const header={querySelector(s){if(s==="[data-graph-navigation]")return anchor;throw Error(s);}};
const document={body:{dataset:{page:row.page}},querySelector(s){if(s===".pa-proof-header")return header;throw Error(s);},createElement(){throw Error("bad graph injection: "+row.name);}};
vm.runInNewContext(input.source+"\\ninitializeGraphNavigation();",{document});});process.stdout.write(String(input.cases.length));'''
    result=subprocess.run(['node','-e',program],input=json.dumps({'source':source[start:end],'cases':cases}),text=True,capture_output=True,check=True,timeout=20)
    assert int(result.stdout)==len(cases)==sum(corpus['node_count'] for corpus in corpora.values())+3


@pytest.mark.parametrize('query,visible',(
    ('',SLUGS),('?view=goal&focus=G007',SLUGS[:2]),('?view=goal&focus=G091',SLUGS[2:]),
    ('?view=family&focus=F01',SLUGS[:2]),('?view=domain&focus=D04',SLUGS[2:]),
    ('?view=goal&focus=G999',SLUGS),('?view=unknown&focus=G007',SLUGS),
))
def test_actual_dispatch_respects_only_known_scales(query,visible,files,drivers):
    document=drivers['Document'](files['grand-campaign/index.html'])
    cards=[attrs for _,attrs in document.tags if 'data-local-family' in attrs]
    source=document.scripts[-1][1]
    program='''const vm=require("node:vm"),input=JSON.parse(require("node:fs").readFileSync(0,"utf8"));
const cards=input.cards.map(attrs=>({attrs,hidden:false,getAttribute(k){return this.attrs[k];}}));
vm.runInNewContext(input.source,{URL,window:{location:{href:"file:///repo/book/_static/constructive-lower-tier-explorer/grand-campaign/"+input.query}},document:{querySelectorAll(s){if(s!=="[data-local-family]")throw Error(s);return cards;}}});
process.stdout.write(JSON.stringify(cards.filter(x=>!x.hidden).map(x=>x.attrs.id)));'''
    result=subprocess.run(['node','-e',program],input=json.dumps({'source':source,'cards':cards,'query':query}),text=True,capture_output=True,check=True,timeout=20)
    assert json.loads(result.stdout)==list(visible)


def test_open_scope_caveats_never_claim_inversion_fubini_or_extension_fields(files,families):
    assert all('full_G007_open' in family.goal_scope for slug,family in families.items() if slug!='prime-field-polynomials')
    assert 'full_G091_open' in families['prime-field-polynomials'].goal_scope
    assert 'Rectangular row/column Fubini' in files['signed-weighted-sums/index.html'].decode()
    assert 'SignedWeightedSum' in families['signed-weighted-sums'].formula
    assert 'SignedAdd(a,b,c)' in families['signed-weighted-sums'].formula
    assert 'x&lt;p' in files['prime-field-polynomials/index.html'].decode()
    assert 'entry zero forced to zero regardless of F(0)' in files['divisor-sums/index.html'].decode()


def test_manifest_is_deterministic_and_covers_every_literal_file(files):
    manifest=json.loads(files['manifest.json'])
    assert manifest['schema']==builder.SCHEMA+'-manifest'
    assert manifest['publication_scope']=='local-only-checkpoint'
    assert manifest['file_count_excluding_manifest']==len(files)-1
    assert manifest['files']=={name:{'bytes':len(payload),'sha256':sha256(payload).hexdigest()}
                              for name,payload in files.items() if name!='manifest.json'}


def test_unregistered_or_empty_tranche_cannot_generate_a_verified_site(monkeypatch):
    monkeypatch.setattr(checkpoints,'CHECKPOINTS',())
    with pytest.raises(builder.ExplorerError,match='must be frozen'):
        builder.families()
    with pytest.raises(checkpoints.CheckpointError):
        builder.build_files()


def test_fake_evidence_object_is_not_accepted(families):
    with pytest.raises(builder.ExplorerError,match='no genuine'):
        builder.family_corpus(families['signed-weighted-sums'],SimpleNamespace())


def test_failed_real_verification_never_proceeds_to_rendering(monkeypatch):
    def reject(*args,**kwargs):raise checkpoints.CheckpointError('the actual proof check rejected')
    monkeypatch.setattr(checkpoints,'verify_checkpoint',reject)
    monkeypatch.setattr(builder,'family_corpus',lambda *_:pytest.fail('rendered a rejected proof'))
    with pytest.raises(checkpoints.CheckpointError,match='actual proof check rejected'):
        builder.build_files()


def test_cli_checks_both_resource_boundaries_and_never_writes_an_overbudget_build(monkeypatch):
    import check_constructive_bottom_layers as guard
    calls=[]
    monkeypatch.setattr(builder.resource,'setrlimit',lambda key,value:calls.append(('cpu',key,value)))
    monkeypatch.setattr(builder.signal,'alarm',lambda seconds:calls.append(('wall',seconds)))
    monkeypatch.setattr(builder,'build_files',lambda:{})
    monkeypatch.setattr(guard,'authoring_rss_bytes',lambda:(_ for _ in ()).throw(RuntimeError('over budget')))
    monkeypatch.setattr(builder.model,'write_or_check',lambda *_a,**_k:pytest.fail('over-budget write'))
    with pytest.raises(RuntimeError,match='over budget'):builder.main([])
    assert calls==[('cpu',builder.resource.RLIMIT_CPU,(170,175)),('wall',180)]


def test_cli_does_not_report_success_after_writer_exceeds_the_memory_budget(monkeypatch,capsys):
    import check_constructive_bottom_layers as guard
    calls=[]
    def check_rss():
        calls.append('rss')
        if calls.count('rss')==2:raise RuntimeError('over budget after snapshot comparison')
        return 1
    monkeypatch.setattr(builder.resource,'setrlimit',lambda *_:None)
    monkeypatch.setattr(builder.signal,'alarm',lambda *_:None)
    monkeypatch.setattr(builder,'build_files',lambda:{})
    monkeypatch.setattr(guard,'authoring_rss_bytes',check_rss)
    monkeypatch.setattr(builder.model,'write_or_check',lambda files,*,output,check:calls.append(('write',files,output,check)))
    with pytest.raises(RuntimeError,match='over budget after snapshot comparison'):builder.main(['--check'])
    assert calls==['rss',('write',{},builder.OUTPUT,True),'rss']
    assert capsys.readouterr().out==''


if __name__=='__main__':
    import resource,signal,time
    from check_constructive_bottom_layers import authoring_rss_bytes
    resource.setrlimit(resource.RLIMIT_CPU,(170,175));signal.alarm(180);started=time.monotonic()
    status=pytest.main(['-q',__file__,*sys.argv[1:]])
    peak=authoring_rss_bytes()
    print(json.dumps({'pytest_status':status,'seconds':time.monotonic()-started,'peak_rss_bytes':peak}),flush=True)
    raise SystemExit(status)
