"""Actual Dirichlet evidence, canonical QR structure and live JS contracts.

Positive rendering invokes fresh original-HA, compiled-Lean and ordinary-root
workers. Combined CLI tests reuse only that same live in-memory build, never
a stored success receipt or a second accepting proof-check implementation.
Actual canonical JavaScript is exercised in the established hostile-SVG DOM
harness. These executable interaction tests are not advertised as visual
browser QA. No production proof checker is stubbed to accept.
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
import build_constructive_dirichlet_explorer as builder
import constructive_dirichlet_checkpoints as checkpoints
import constructive_bottom_layer_checkpoints as previous
from constructive_dirichlet_definitions import ALL_CONSTRUCTIVE_DEFINITIONS_BY_NAME as DEFINITIONS
from constructive_formula_compactor import _LocalDefinedParser
from peano_lab.kernel.formulas import parse_formula_with_names


SLUGS=('finite-support','dirichlet-convolution','dirichlet-fubini','dirichlet-units','mobius-inversion')
EXPECTED_COUNTS=dict(zip(SLUGS,(8,40,32,25,8),strict=True))
EXPECTED_PREFIXES=dict(zip(SLUGS,('ZS','DC','DF','DU','MI'),strict=True))
ROOT_TAGS={
    'finite-support':{'signed_prefix_sum_zero_tail':'ZS0004','signed_prefix_sum_last_value':'ZS0007','signed_prefix_sum_zero_padding_iff':'ZS0008'},
    'dirichlet-convolution':{'dirichlet_convolution_table_exists_extensionally_unique':'DC001D','dirichlet_convolution_table_commutative':'DC0024','dirichlet_convolution_padded_prefix_iff':'DC0028'},
    'dirichlet-fubini':{'dirichlet_convolution_fubini_interchange':'DF001D','dirichlet_convolution_associative':'DF001E','dirichlet_convolution_associative_tables_exists':'DF0020'},
    'dirichlet-units':{'dirichlet_delta_unit_exists':'DU0013','dirichlet_constant_one_sum_iff':'DU0018','dirichlet_constant_one_realizes_divisor_sum':'DU0019'},
    'mobius-inversion':{'mobius_inversion_for_actual_mobius_table':'MI0005','mobius_inversion_arithmetic_tables':'MI0006','mobius_inversion_iff':'MI0008'},
}
PRINCIPAL_CONTRACTS=(
    ('finite-support','signed_prefix_sum_zero_tail',
     'forall F k l a b. Le(k,l) -> SignedZeroWindow(F,k,l) -> SignedPrefixSum(F,k,a) -> SignedPrefixSum(F,l,b) -> a=b'),
    ('dirichlet-convolution','dirichlet_convolution_table_exists_extensionally_unique',
     'forall N F G. ArithTable(N,F) -> ArithTable(N,G) -> exists H. DirichletTable(N,F,G,H) /\\ (forall K. DirichletTable(N,F,G,K) -> ArithPositiveEqual(H,K,N))'),
    ('dirichlet-fubini','dirichlet_convolution_associative',
     'forall N F G H A B n u v. DirichletTable(N,F,G,A) -> DirichletTable(N,G,H,B) -> ~(n=0) -> Le(n,N) -> DirichletSum(A,H,n,u) -> DirichletSum(F,B,n,v) -> u=v'),
    ('dirichlet-units','dirichlet_constant_one_sum_iff',
     'forall N F U n z. ArithTable(N,F) -> ConstantOneTable(N,U) -> ~(n=0) -> Le(n,N) -> (DirichletSum(F,U,n,z) -> DivisorSum(F,n,z)) /\\ (DivisorSum(F,n,z) -> DirichletSum(F,U,n,z))'),
    ('mobius-inversion','mobius_inversion_arithmetic_tables',
     'forall N F G. ArithTable(N,F) -> ArithTable(N,G) -> DivisorTransform(N,F,G) -> exists M H. MobiusTable(N,M) /\\ (DirichletTable(N,M,G,H) /\\ ArithPositiveEqual(H,F,N))'),
    ('mobius-inversion','mobius_inversion_iff',
     'forall N F G M. ArithTable(N,F) -> ArithTable(N,G) -> MobiusTable(N,M) -> (DivisorTransform(N,F,G) -> DirichletTable(N,M,G,F)) /\\ (DirichletTable(N,M,G,F) -> DivisorTransform(N,F,G))'),
)


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
def files(pytestconfig):
    # Real proof checks. No sidecar, class instance, or admission Boolean is a
    # substitute for the original complete HA check and actual Lean process.
    supplied=getattr(pytestconfig,'_dirichlet_fresh_snapshot',None)
    if supplied is None:
        before=builder._immutable_test_state()
        result=builder.build_files()
    else:
        assert type(supplied) is builder._FreshSnapshotTests
        assert supplied.binding==builder._assert_snapshot_binding(supplied.files)
        before=supplied.immutable_before
        result=supplied.files
    assert builder._immutable_test_state()==before
    builder.model.write_or_check(result,output=builder.OUTPUT,check=True)
    return result


@pytest.fixture(scope='module')
def corpora(files):
    return {slug:json.loads(files[slug+'/api/corpus.json']) for slug in SLUGS}


@pytest.fixture(scope='module')
def theorem_table():
    # The same actual source inventory serves every family. Final source
    # binding still surrounds the whole test run; no theorem is substituted.
    return {row.name:row for row in (*builder.closure.parent_snapshot().specs,
                                    *builder.previous_rows(),*checkpoints.all_new_rows())}


def test_exact_inventory_and_separate_non_admitting_membership(files,corpora):
    inventory=json.loads(files['checkpoints.json'])
    expected=checkpoints.all_new_rows()
    assert inventory['schema']==builder.SCHEMA
    assert inventory['publication_scope']=='local-only-checkpoint'
    assert inventory['published'] is inventory['alpha_admission_performed'] is inventory['stable_admission_performed'] is False
    assert inventory['inherited_support_counted_as_new'] is False
    assert inventory['previous_research_theorems']==421
    assert inventory['previous_research_generations']==[170,126,125]
    assert inventory['prior_theorem_count_for_exact_ast_novelty_check']==3643
    assert inventory['parent']['alpha_version']=='v30'
    assert inventory['parent']['alpha_checked_use_count']==3222
    assert inventory['parent']['stable_count']==432
    assert inventory['parent']['catalog_sha256']=='ac7111ec14ff07bf899238ed465de337e6d76e9343384947022360dc7e65d9f7'
    assert inventory['navigation_revision']=='ac7111ec14ff'
    assert inventory['new_theorems']==sum(corpus['node_count'] for corpus in corpora.values())==len(expected)==113
    assert {slug:corpus['node_count'] for slug,corpus in corpora.items()}==EXPECTED_COUNTS
    assert Counter(row['name'] for corpus in corpora.values() for row in corpus['nodes'])==Counter(row.name for row in expected)
    assert inventory['statement_asts_distinct_from_all_3643_prior_and_each_other'] is True
    assert len({row.name for row in expected})==len(expected)


@pytest.mark.parametrize('slug',SLUGS)
def test_new_rows_never_launder_inherited_research_into_alpha(slug,files,corpora,families,theorem_table):
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
    assert all(row['complete_ordinary_ha_checked'] is True
               and type(row['ordinary_certificate_nodes']) is int
               and 1<row['ordinary_certificate_nodes']<=builder.closure.DEFAULT_LAYERED_REPLAY_LIMITS.max_candidate_proof_occurrences
               for row in report['principal_roots'])
    assert corpus['render_evidence_provenance']=='projection_of_fresh_nonce_authenticated_workers_and_exact_pinned_proof_data'
    assert {row['name'] for row in corpus['nodes']}=={row.name for row in owned}
    assert all(row['inventory_role']=='new_owned_theorem' for row in corpus['nodes'])
    for record in (corpus,*corpus['nodes']):
        assert builder.render._status(record)==builder.render.STATUS
        assert all(record[key] is False for key in builder.render.FORBIDDEN_ADMISSION_FIELDS)
        assert 'alpha_edition_version' not in record and 'alpha_first_enrolled_version' not in record
    assert corpus['alpha_enrolled_node_count']==corpus['alpha_checked_use_node_count']==corpus['stable_admitted_node_count']==0
    support=report['support']
    assert support['published_non_admitted_count']==support['prior_bottom_layer_count']+support['prior_lower_tier_count']
    assert support['counted_as_new_owned_theorems'] is False
    assert (support['published_non_admitted_count']+support['local_non_admitted_count']+support['current_cross_track_count']+
            support['alpha_v30_count']+len(owned)+1)==report['bundle']['nodes_including_packaging_root']
    by_name=theorem_table
    for external in corpus['external_dependencies']:
        name=external['name']
        assert external['counted_as_new_owned_theorem'] is False
        assert external['statement']==by_name[name].statement
        assert external['statement_sha256']==sha256(by_name[name].statement.encode()).hexdigest()
        admitted=external['inventory_role']=='inherited_alpha_v30'
        assert external['admitted_to_alpha'] is external['alpha_checked_use'] is external['enrolled_in_alpha'] is admitted
        if not admitted:
            assert external['parent_alpha_version'] is None
            expected_role=('inherited_published_bottom_layer_checkpoint' if name in support['prior_bottom_layer_theorems']
                           else 'inherited_published_lower_tier_checkpoint' if name in support['prior_lower_tier_theorems']
                           else 'inherited_local_lower_continuation_checkpoint' if name in support['prior_lower_continuation_theorems']
                           else 'new_cross_track_support')
            assert external['inventory_role']==expected_role
    assert corpus['root_names']==list(families[slug].roots)
    assert {name:corpus['tags'][name] for name in corpus['root_names']}==ROOT_TAGS[slug]
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
    if slug=='dirichlet-convolution':
        companion='dirichlet-commutativity-rfc-v1.md'
        assert files['sources/'+companion]==(ROOT/'research/arithmetic-library'/companion).read_bytes()
        assert ('../sources/'+companion+'?v='+builder.HTML_REVISION).encode() in files[slug+'/checkpoint.html']


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


def test_actual_convolution_graphs_are_not_disguised_sum_oracles(corpora):
    definitions={row['name']:row for row in corpora['dirichlet-convolution']['definitions']}
    for name,parameters in (('DirichletEntry',('F','G','n','d','z')),('DirichletPrefix',('F','G','n','l','M')),
                            ('DirichletSum',('F','G','n','z')),('DirichletTable',('N','F','G','H'))):
        row=definitions[name]
        assert row['parameters']==list(parameters)
        assert row['expanded_template']==DEFINITIONS[name].template_source
        assert row['id']==DEFINITIONS[name].stable_id
    assert 'SignedMul' in definitions['DirichletEntry']['dependency_names']
    assert 'DirichletEntry' in definitions['DirichletPrefix']['dependency_names']
    assert 'SignedPrefixSum' in definitions['DirichletSum']['dependency_names']
    assert 'DirichletSum' in definitions['DirichletTable']['dependency_names']


@pytest.mark.parametrize('slug,name,contract',PRINCIPAL_CONTRACTS)
def test_independently_written_principal_contract_is_the_exact_displayed_statement(slug,name,contract,corpora):
    corpus=corpora[slug]
    node=next(row for row in corpus['nodes'] if row['name']==name)
    definitions={row['name']:DEFINITIONS[row['name']] for row in corpus['definitions']}
    parser=_LocalDefinedParser(contract,definitions)
    assert parser.parse()==parse_formula_with_names(node['statement'])[0]
    assert not parser.free


def test_inversion_has_actual_convolution_cancellation_and_unit_ancestors(corpora):
    support=corpora['mobius-inversion']['checkpoint_report']['support']
    assert 'mobius_divisor_sum_cancellation' in support['prior_lower_continuation_theorems']
    assert 'dirichlet_convolution_associative' in support['current_cross_track_theorems']
    assert 'dirichlet_delta_left_table' in support['current_cross_track_theorems']
    assert 'dirichlet_constant_one_sum_iff' in support['current_cross_track_theorems']
    assert support['local_non_admitted_count']==len(support['prior_lower_continuation_theorems'])
    assert support['published_non_admitted_count']==support['prior_bottom_layer_count']+support['prior_lower_tier_count']


def test_new_definitions_preserve_all_old_mobius_and_fubini_identities(corpora):
    import constructive_lower_continuation_definitions as old
    assert len(old.ALL_CONSTRUCTIVE_DEFINITIONS_BY_NAME)==356
    for name,definition in old.ALL_CONSTRUCTIVE_DEFINITIONS_BY_NAME.items():
        assert DEFINITIONS[name] is definition
    mobius={row['name']:row for row in corpora['mobius-inversion']['definitions']}
    assert mobius['MobiusTable']['id']=='ND0265'
    assert mobius['MobiusTable']['expanded_template']==DEFINITIONS['MobiusTable'].template_source
    assert mobius['DivisorTransform']['parameters']==['N','F','G']
    assert mobius['DivisorTransform']['dependency_names']==['Le','ArithAt','DivisorSum']
    for name in ('ConstantOneTable','KroneckerDeltaTable'):
        assert not {'DirichletSum','DirichletTable','DivisorTransform','MobiusTable'}.intersection(mobius[name]['dependency_names'])
    grid={row['name']:row for row in corpora['dirichlet-fubini']['definitions']}
    for name in ('ArithSlice','SignedSliceSum','ArithRowSums','SignedRectangularSum'):
        assert grid[name]['id']==old.ALL_CONSTRUCTIVE_DEFINITIONS_BY_NAME[name].stable_id
        assert grid[name]['expanded_template']==old.ALL_CONSTRUCTIVE_DEFINITIONS_BY_NAME[name].template_source


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
    used_bottom=used_lower=used_local=used_cross=used_atlas=0
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
                    assert (target=='../constructive-gaussian-campaign/index.html' or target.startswith('../constructive-bottom-layer-explorer/')
                            or target.startswith('../constructive-lower-tier-explorer/')
                            or target.startswith('../constructive-lower-continuation-explorer/')),(name,attrs[key])
                    path=builder.OUTPUT/target
                    assert path.is_file(),(name,attrs[key])
                    if target.startswith('../constructive-bottom-layer-explorer/'):
                        used_bottom+=1
                    elif target.startswith('../constructive-lower-tier-explorer/'):used_lower+=1
                    elif target.startswith('../constructive-lower-continuation-explorer/'):used_local+=1
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
    assert used_bottom>0 and used_lower>0 and used_local>0 and used_cross>0 and used_atlas>0


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
    assert int(result.stdout)==len(scripts)==17


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
    assert int(result.stdout)==len(cases)==sum(corpus['node_count'] for corpus in corpora.values())+5


@pytest.mark.parametrize('query,visible',(
    ('',SLUGS),('?view=goal&focus=G007',(SLUGS[0],*SLUGS[2:])),('?view=goal&focus=G009',SLUGS[1:4]),
    ('?view=family&focus=F01',SLUGS),('?view=domain&focus=D01',SLUGS),
    ('?view=goal&focus=G999',SLUGS),('?view=unknown&focus=G007',SLUGS),
))
def test_actual_dispatch_respects_only_known_scales(query,visible,files,drivers):
    document=drivers['Document'](files['grand-campaign/index.html'])
    cards=[attrs for _,attrs in document.tags if 'data-local-family' in attrs]
    source=document.scripts[-1][1]
    program='''const vm=require("node:vm"),input=JSON.parse(require("node:fs").readFileSync(0,"utf8"));
const cards=input.cards.map(attrs=>({attrs,hidden:false,getAttribute(k){return this.attrs[k];}}));
vm.runInNewContext(input.source,{URL,window:{location:{href:"file:///repo/book/_static/constructive-dirichlet-explorer/grand-campaign/"+input.query}},document:{querySelectorAll(s){if(s!=="[data-local-family]")throw Error(s);return cards;}}});
process.stdout.write(JSON.stringify(cards.filter(x=>!x.hidden).map(x=>x.attrs.id)));'''
    result=subprocess.run(['node','-e',program],input=json.dumps({'source':source,'cards':cards,'query':query}),text=True,capture_output=True,check=True,timeout=20)
    assert json.loads(result.stdout)==list(visible)


def test_full_G007_is_distinct_from_open_G009_and_G091(files,families):
    assert families['mobius-inversion'].goal_scope=='full_G007_finite_signed_mobius_inversion_locally_proved'
    assert all(families[slug].goal_scope.endswith('full_G009_open') for slug in ('dirichlet-convolution','dirichlet-fubini','dirichlet-units'))
    inversion=files['mobius-inversion/index.html'].decode()
    assert 'N=0' in inversion and 'F(0)' in inversion and 'G(0)' in inversion
    assert 'Full finite signed G007 is proved locally' in inversion
    inventory=json.loads(files['checkpoints.json'])
    assert inventory['full_G007_inversion_proved'] is True
    assert inventory['full_G009_dirichlet_convolution_theory_proved'] is inventory['general_G091_prime_power_fields_proved'] is False


def test_manifest_is_deterministic_and_covers_every_literal_file(files):
    manifest=json.loads(files['manifest.json'])
    assert manifest['schema']==builder.SCHEMA+'-manifest'
    assert manifest['publication_scope']=='local-only-checkpoint'
    assert manifest['file_count_excluding_manifest']==len(files)-1
    assert manifest['files']=={name:{'bytes':len(payload),'sha256':sha256(payload).hexdigest()}
                              for name,payload in files.items() if name!='manifest.json'}


def test_saved_audit_is_an_exact_output_of_all_fifteen_fresh_ordinary_root_checks(files):
    from check_constructive_bottom_layers import canonical_report
    report=json.loads(files['proof-audit.json'])
    inventory=json.loads(files['checkpoints.json'])
    assert files['proof-audit.json']==canonical_report(report).encode('utf-8')
    assert report['proof_authority']=='fresh_original_ha_and_independent_compiled_lean_checks'
    assert report['stored_receipt_is_proof_authority'] is False
    assert report['published'] is report['alpha_admission_performed'] is report['stable_admission_performed'] is False
    assert report['checkpoints']==inventory['checkpoints']
    assert report['new_theorems']==113 and report['prior_theorem_count_for_exact_ast_novelty_check']==3643
    assert report['statement_asts_distinct_from_prior_and_within_tranche'] is True
    roots=[root for family in report['checkpoints'] for root in family['principal_roots']]
    assert len(roots)==15 and all(root['complete_ordinary_ha_checked'] is True for root in roots)
    assert report['full_G007_inversion_proved'] is True
    assert report['full_G009_dirichlet_convolution_theory_proved'] is report['general_G091_prime_power_fields_proved'] is False
    assert inventory['render_source_binding_sha256']==builder._render_binding()


def test_render_projection_is_not_a_fabricated_kernel_receipt():
    import inspect
    assert 'receipt' not in builder._FreshRenderEvidence.__dataclass_fields__
    assert set(builder._FreshRenderEvidence.__dataclass_fields__)=={'checkpoint','selection','bundle','report'}
    for function in (builder._render_files,builder._fresh_projection):
        tree=ast.parse(inspect.getsource(function))
        calls={node.func.id if isinstance(node.func,ast.Name) else node.func.attr
               for node in ast.walk(tree) if isinstance(node,ast.Call)
               and isinstance(node.func,(ast.Name,ast.Attribute))}
        assert not {'CheckedProofBundle','check_proof_bundle','check_bottom_layer_bundle',
                    'verify_checkpoint','replay_bottom_layer_theorem','select_support','_expected_family_report'} & calls
    tree=ast.parse(inspect.getsource(builder._build_verified))
    calls=sorted((node for node in ast.walk(tree) if isinstance(node,ast.Call)
                  and isinstance(node.func,(ast.Name,ast.Attribute))),key=lambda node:node.lineno)
    names=[node.func.id if isinstance(node.func,ast.Name) else node.func.attr for node in calls]
    assert names.index('verify_in_fresh_windows')<names.index('_fork_render_phase')
    tree=ast.parse(inspect.getsource(builder._render_files))
    calls=sorted((node for node in ast.walk(tree) if isinstance(node,ast.Call)
                  and isinstance(node.func,(ast.Name,ast.Attribute))),key=lambda node:node.lineno)
    names=[node.func.id if isinstance(node.func,ast.Name) else node.func.attr for node in calls]
    assert names.index('_fresh_projection')<names.index('family_corpus')
    assert names.count('_render_binding')==2


@pytest.mark.parametrize('bad',({},None,[],{'checkpoints':[],'full_G007_inversion_proved':False}))
def test_partial_or_unverified_audit_cannot_enter_render_projection(bad):
    with pytest.raises(builder.ExplorerError,match='complete fresh audit'):
        builder._validate_fresh_audit(bad)


def test_unregistered_or_empty_tranche_cannot_generate_a_verified_site(monkeypatch):
    monkeypatch.setattr(checkpoints,'CHECKPOINTS',())
    with pytest.raises(builder.ExplorerError,match='must be frozen'):
        builder.families()
    with pytest.raises(builder.ExplorerError,match='must be frozen'):
        builder.build_files()


@pytest.mark.parametrize('mutation',('partial','duplicate','unknown','reordered'))
def test_incomplete_or_ambiguous_checkpoint_inventory_fails_before_verification(monkeypatch,mutation):
    from dataclasses import replace
    original=checkpoints.CHECKPOINTS
    changed=(original[:-1] if mutation=='partial' else
             original+(original[0],) if mutation=='duplicate' else
             tuple(reversed(original)) if mutation=='reordered' else
             (*original[:-1],replace(original[-1],slug='unreviewed-extra-family')))
    monkeypatch.setattr(checkpoints,'CHECKPOINTS',changed)
    monkeypatch.setattr(builder.audit,'verify_in_fresh_windows',lambda:pytest.fail('checked an invalid inventory'))
    with pytest.raises(builder.ExplorerError,match='must be frozen'):
        builder.build_files()


def test_fake_evidence_object_is_not_accepted():
    with pytest.raises(builder.ExplorerError,match='no genuine'):
        builder.family_corpus(SimpleNamespace(),SimpleNamespace())


def test_failed_real_verification_never_proceeds_to_rendering(monkeypatch):
    def reject(*args,**kwargs):raise checkpoints.CheckpointError('the actual proof check rejected')
    monkeypatch.setattr(builder.audit,'verify_in_fresh_windows',reject)
    monkeypatch.setattr(builder,'family_corpus',lambda *_:pytest.fail('rendered a rejected proof'))
    with pytest.raises(checkpoints.CheckpointError,match='actual proof check rejected'):
        builder.build_files()


def test_cli_checks_both_resource_boundaries_and_never_writes_an_overbudget_build(monkeypatch):
    calls=[]
    monkeypatch.setattr(builder.resource,'setrlimit',lambda key,value:calls.append(('cpu',key,value)))
    monkeypatch.setattr(builder.signal,'alarm',lambda seconds:calls.append(('wall',seconds)))
    monkeypatch.setattr(builder,'_build_verified',lambda **_k:(_ for _ in ()).throw(RuntimeError('over budget')))
    monkeypatch.setattr(builder.model,'write_or_check',lambda *_a,**_k:pytest.fail('over-budget write'))
    with pytest.raises(RuntimeError,match='over budget'):builder.main([])
    assert calls==[('cpu',builder.resource.RLIMIT_CPU,(170,175)),('wall',builder.CONTROLLER_WALL_SECONDS)]
    assert builder.audit.CONTROLLER_WALL_SECONDS==21*185+180==4065
    assert builder.CONTROLLER_WALL_SECONDS==4250
    assert builder.audit.WALL_SECONDS==180 and builder.audit.CPU_LIMITS==(170,175)


def test_cli_does_not_report_success_after_writer_exceeds_the_memory_budget(monkeypatch,capsys,tmp_path):
    import check_constructive_bottom_layers as guard
    calls=[]
    def check_rss():
        calls.append('rss')
        if calls.count('rss')==2:raise RuntimeError('over budget after snapshot comparison')
        return 1
    monkeypatch.setattr(builder,'_render_files',lambda *_:{})
    monkeypatch.setattr(guard,'authoring_rss_bytes',check_rss)
    monkeypatch.setattr(builder.model,'write_or_check',lambda files,*,output,check:calls.append(('write',files,output,check)))
    with pytest.raises(RuntimeError,match='over budget after snapshot comparison'):
        builder._render_child({}, {}, 'transport-only',output=tmp_path,check=True,test=False,write_audit=False,
                              immutable_before=({},()),nonce='0'*64,write_fd=-1)
    assert calls==['rss',('write',{},tmp_path,True),'rss']
    assert capsys.readouterr().out==''



def test_full_inversion_display_rejects_real_bundle_evidence_without_ordinary_roots(files):
    from peano_lab.library.proof_bundle import decode_proof_bundle
    checkpoint=next(row for row in checkpoints.CHECKPOINTS if row.slug=='mobius-inversion')
    report=json.loads(files['mobius-inversion/api/checkpoint.json'])
    for root in report['principal_roots']:
        root['complete_ordinary_ha_checked']=False
        del root['ordinary_certificate_nodes']
    # The unchanged original bundle remains real; removing its separately
    # obtained ordinary-root evidence must still stop the display projection.
    bundle,_=decode_proof_bundle(files['checkpoints/'+Path(checkpoint.artifact).name].decode('utf-8'))
    # The ordinary-evidence guard precedes any use of display-only selection;
    # no actual proof checker or successful evidence provider is replaced.
    rejected=builder._FreshRenderEvidence(checkpoint,None,bundle,report)
    family=next(item for item in builder.families() if item.slug==checkpoint.slug)
    with pytest.raises(builder.ExplorerError,match='ordinary principal'):
        builder.family_corpus(family,rejected)


@pytest.mark.parametrize('kind',('file','directory','live_symlink','dangling_symlink'))
def test_cli_never_overwrites_an_existing_or_symlink_audit(kind,tmp_path,monkeypatch):
    receipt=tmp_path/'audit.json';target=tmp_path/'target.json';original=b'previous audit bytes\n'
    if kind=='file':receipt.write_bytes(original)
    elif kind=='directory':receipt.mkdir()
    else:
        if kind=='live_symlink':target.write_bytes(original)
        receipt.symlink_to(target)
    monkeypatch.setattr(builder.audit,'RECEIPT',receipt)
    monkeypatch.setattr(builder,'_build_verified',lambda **_k:pytest.fail('unnecessary fresh proof run before refusing overwrite'))
    with pytest.raises(SystemExit) as error:builder.main(['--write-audit'])
    assert error.value.code==2
    if kind=='file':assert receipt.read_bytes()==original
    elif kind=='directory':assert receipt.is_dir() and not tuple(receipt.iterdir())
    else:
        assert receipt.is_symlink()
        if kind=='live_symlink':assert target.read_bytes()==original
        else:assert not target.exists()


def test_combined_test_mode_passes_the_same_in_memory_files_not_a_receipt_path(files,monkeypatch):
    calls=[]
    def record(args,*,plugins):
        calls.append((args,plugins))
        return 17
    monkeypatch.setattr(pytest,'main',record)  # Pytest scheduling, never proof acceptance.
    before=builder._immutable_test_state()
    assert builder._run_snapshot_tests(files,before)==17
    arguments,plugins=calls.pop()
    assert arguments==['-q',str(ROOT/'peano-lab/py/tests/test_constructive_dirichlet_explorer.py')]
    assert len(plugins)==1 and type(plugins[0]) is builder._FreshSnapshotTests
    assert plugins[0].files is files and plugins[0].immutable_before==before
    assert plugins[0].binding==builder._assert_snapshot_binding(files)
    config=SimpleNamespace();plugins[0].pytest_configure(config)
    assert config._dirichlet_fresh_snapshot is plugins[0]
    assert not calls


def test_in_memory_test_handoff_registers_with_the_real_pytest_plugin_manager():
    # Exercise scheduling only: this empty object is never used to render or
    # prove anything. Pluggy requires identity-hashable plugin instances.
    plugin=builder._FreshSnapshotTests({},'scheduling-only',({},()))
    manager=pytest.PytestPluginManager()
    manager.register(plugin)
    assert plugin in manager.get_plugins()
    config=SimpleNamespace();plugin.pytest_configure(config)
    assert config._dirichlet_fresh_snapshot is plugin


if __name__=='__main__':
    import resource,signal,time
    from check_constructive_bottom_layers import authoring_rss_bytes
    resource.setrlimit(resource.RLIMIT_CPU,(170,175));signal.alarm(builder.CONTROLLER_WALL_SECONDS);started=time.monotonic()
    status=pytest.main(['-q',__file__,*sys.argv[1:]])
    peak=authoring_rss_bytes()
    print(json.dumps({'pytest_status':status,'seconds':time.monotonic()-started,'peak_rss_bytes':peak}),flush=True)
    raise SystemExit(status)
