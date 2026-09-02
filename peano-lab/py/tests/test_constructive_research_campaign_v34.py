"""Pure v34 atlas projection and strict same-live publication assertions.

Standalone fixtures are explicitly display-only. Actual source statements may
be read, but fabricated catalogue/header observations never mint a capability.
The release plugin calls the same read-only assertions with genuine evidence.
"""
from __future__ import annotations

import ast
from collections.abc import Mapping
from copy import deepcopy
from hashlib import sha256
import inspect
import json
from pathlib import Path
import re
import subprocess
import sys
from types import SimpleNamespace

import pytest

ROOT=Path(__file__).resolve().parents[3]
sys.path.insert(0,str(ROOT/'scripts'))
import extend_constructive_research_campaign_v34 as atlas
from sync_constructive_grand_campaign import _definition_dags, _milestone_dag, validate_campaign_dags
from tests.test_constructive_research_campaign_v32 import _function, _node

NOTICE='PRIVATE DISPLAY FIXTURE ONLY; NOT A VERIFIED CATALOGUE, PROOF OR RELEASE'
PINS={
    'campaign.json':(736201,'a4cce950e1402dd32129241c39e287142a91c52f91646e9ba44fba4bac06755f'),
    'definitions.json':(1489692,'7210608913bdb601c055684090bd667704ae66d46be3a71d07818e092de5c15d'),
    'dag-audit.json':(8466,'d85f1afe5311efc6f09d05ecb69ce768540333abf91d74d07110bd0e1d8e4b84'),
    'index.html':(774916,'f5fa8a047f510a3971f64d280f2980752b2d1613d8e72ea09ed8af59e81ce7ec'),
}
DEFINITIONS={
    'ND0341':'PolynomialShift','ND0342':'FpPolynomialRightDivides',
    'ND0343':'CommonRepresentatives','ND0344':'FpPolynomialAlignedAdd',
    'ND0345':'FpPolynomialAlignedSubtract','ND0346':'FpPolynomialCommonRightDivisor',
    'ND0347':'FpPolynomialBezoutRepresentation','ND0348':'FpPolynomialZeroOrMonic',
    'ND0349':'FpPolynomialRightGcd','ND0350':'FpPolynomialNormalizedGcd',
}
OLD_DIVISION_IDS=tuple('ND%04d'%n for n in range(334,341))
GCD_FLAGS=('division_execution_proved','execution_uniqueness_proved',
    'formal_representation_congruence_proved','normalized_gcd_existence_proved',
    'bezout_identity_proved','gcd_greatestness_proved','normalized_gcd_equivalent_uniqueness_proved',
    'polynomial_associativity_proved','polynomial_gcd_bezout_proved')
CONGRUENCE_FLAGS=('bounded_solution_bijection_proved','zero_modulus_explicit',
                  'modulus_one_explicit','fermat_all_inputs_proved')

def _goal(campaign,identifier):
    return next(row for row in campaign['nodes'] if row['id']==identifier)

def _thaw(value):
    if isinstance(value,Mapping):return {k:_thaw(v) for k,v in value.items()}
    if isinstance(value,(tuple,list)):return [_thaw(v) for v in value]
    return value

@pytest.mark.parametrize('name',tuple(PINS))
def test_four_exact_historical_parent_documents(name):
    raw=atlas.parent_files()[name]
    assert (len(raw),sha256(raw).hexdigest())==PINS[name]
    assert atlas.PARENT_PINS[name]==dict(bytes=PINS[name][0],sha256=PINS[name][1])

@pytest.fixture(scope='module')
def formatting():
    parents=atlas.parent_files()
    original,old_graph,old_audit=atlas._parent(parents)
    routes=atlas._package_map(atlas.publication._all_family_metadata())
    # Real source syntax, deliberately NON-authorizing invented display headers.
    specs={r.name:r for r in atlas.research.research_specs()}
    rows=[dict(name='private_display_parent_%d'%i,statement='0=1',fixture_notice=NOTICE) for i in range(4092)]
    reports={}
    for family in atlas.research.FAMILIES:
        positions={name:i for i,name in enumerate(family.ordered_cone_names)}
        family_rows=[]
        for name in family.owned_names:
            statement=specs[name].statement
            row=dict(name=name,statement=statement,statement_sha256=sha256(statement.encode()).hexdigest(),
                checked_use=True,body_checked=True,membership='alpha_only',evidence_status='alpha_closed',
                empty_context_closure=dict(status='checked',kernel_mode='intuitionistic',
                    certificate_sha256=family.artifact_sha256,bundle_node_id=positions[name]),
                alpha_v34_frontier_enrollment=dict(first_enrolled_version='v34',campaign=family.slug,
                    bundle_sha256=family.artifact_sha256,bundle_node_id=positions[name]),fixture_notice=NOTICE)
            rows.append(row)
            family_rows.append(dict(name=name,node_id=positions[name],statement_sha256=row['statement_sha256']))
        reports[family.slug]=dict(slug=family.slug,new_theorem_count=family.count,
            specs_sha256=family.specs_sha256,owned_node_ids={n:positions[n] for n in family.owned_names},
            rows=family_rows,bundle=dict(path=family.artifact,bytes=family.artifact_bytes,
                sha256=family.artifact_sha256,nodes_including_packaging_root=family.node_count,
                dependency_edges_including_packaging=family.bundle_edges,body_proof_nodes=family.body_nodes,
                kernel_calls=family.node_count,original_ha_checked=True,independent_lean_checked=True),
            principal_roots=[dict(name=n,node_id=positions[n],statement_sha256=specs[n] and sha256(specs[n].statement.encode()).hexdigest(),
                complete_ordinary_ha_checked=True,ordinary_certificate_nodes=2) for n in family.principal_roots],
            fixture_notice=NOTICE)
    catalog=dict(schema='peano-library-alpha-snapshot-v34',theorem_count=4223,checked_use_count=4223,
        stable_count=432,edge_count=13816,theorems=rows,layer_count=53,edition_identity_sha256='b'*64,
        ordered_enrollment_root_sha256='c'*64,evidence_root_sha256='d'*64,fixture_notice=NOTICE)
    campaign=atlas._project(original,catalog,reports,'a'*64,'e'*64,routes)
    campaign['meta']['fixture_notice']=NOTICE
    graph=atlas._graph(old_graph,campaign,routes)
    html=atlas._html(parents['index.html'].decode(),campaign,graph,routes,'a'*12)
    return SimpleNamespace(parents=parents,original=original,old_graph=old_graph,old_audit=old_audit,
        catalog=catalog,reports=reports,campaign=campaign,graph=graph,html=html,routes=routes,
        catalog_sha256='a'*64,source_binding_sha256='e'*64,revision='a'*12,fixture_notice=NOTICE)

def _assert_preservation(original,campaign):
    assert _milestone_dag(campaign)==_milestone_dag(original)
    assert len(campaign['nodes'])==144 and sum(n['id'].startswith('G') for n in campaign['nodes'])==120
    assert campaign['definitions']==original['definitions']
    assert campaign['sources'][:len(original['sources'])]==original['sources']
    for before,after in zip(original['nodes'],campaign['nodes'],strict=True):
        if before['id'] not in ('G091','G012'):assert before==after
        else:
            for key in ('id','status','statement','deps','title','family','layer','difficulty'):
                assert before.get(key)==after.get(key)
    assert _goal(campaign,'G009')==_goal(original,'G009')
    assert _goal(campaign,'G009')['evidence']['alpha_first_enrolled_version']=='v32'
    g12,old12=_goal(campaign,'G012'),_goal(original,'G012')
    assert g12['evidence']==old12['evidence'] and g12['evidence']['alpha_version']=='v19'
    assert g12['evidence']['theorem_name']=='linear_congruence_solvable_iff_gcd_divides'
    assert g12['historical_v33_linear_solvability']['record']==old12
    assert g12['additional_checked_chapters'][:-1]==old12.get('additional_checked_chapters',[])
    g91,old91=_goal(campaign,'G091'),_goal(original,'G091')
    assert g91['historical_v33_polynomial_progress']['record']==old91
    assert g91['polynomial_prerequisite_progress']==old91['polynomial_prerequisite_progress']
    assert g91['polynomial_euclidean_progress']==old91['polynomial_euclidean_progress']
    assert g91['additional_checked_chapters'][:-1]==old91['additional_checked_chapters']
    assert g91['status']=='open' and 'evidence' not in g91

def test_both_new_components_preserve_actual_old_admission_and_milestones(formatting):
    _assert_preservation(formatting.original,formatting.campaign)
    atlas._preserved(formatting.original,formatting.campaign)

def test_407_reviewed_definitions_preserve_all397_original_objects(formatting):
    old={r['id']:r for r in formatting.old_graph['reviewed_definitions']}
    new={r['id']:r for r in formatting.graph['reviewed_definitions']}
    assert len(old)==397 and len(new)==407 and set(new)-set(old)==set(DEFINITIONS)
    assert {key:new[key] for key in old}==old
    assert {key:new[key]['name'] for key in DEFINITIONS}==DEFINITIONS
    assert all(new[key]['route']=='polynomial-gcd-bezout' for key in DEFINITIONS)
    assert sum(len(r['dependencies']) for r in old.values())==865
    assert sum(len(r['dependencies']) for r in new.values())==884
    assert _definition_dags(formatting.campaign,formatting.graph)[2:4]==(855,884)
    assert formatting.graph['definition_page_overrides']==formatting.old_graph['definition_page_overrides']
    for key in ('definitions','definition_edges','milestone_usage_edges','authority_policy'):
        assert formatting.graph[key]==formatting.old_graph[key]

@pytest.mark.parametrize('field,value',(
    ('alpha_version','v33'),('alpha_first_enrolled_version','v33'),('alpha_enrolled',False),
    ('checked_use',False),('stable_member',True),('full_G091_proved',True),('new_theorem_count',118),
    ('polynomial_associativity_proved',False),('polynomial_gcd_bezout_proved',False),
    ('normalized_gcd_existence_proved',False),('bezout_identity_proved',False),
    ('gcd_greatestness_proved',False),('normalized_gcd_equivalent_uniqueness_proved',False),
    ('arbitrary_identity_pair_quotient_uniqueness_proved',True)))
def test_gcd_javascript_guard_rejects_each_wrong_boundary(formatting,field,value):
    original=_goal(formatting.campaign,'G091');bad=deepcopy(original)
    bad['polynomial_gcd_progress'][field]=value
    result=_node(_function(formatting.html.decode(),'currentPolynomialGcdProgress')+'\n'+
        'process.stdout.write(JSON.stringify(['+'currentPolynomialGcdProgress('+json.dumps(original)+'),'+
        'currentPolynomialGcdProgress('+json.dumps(bad)+')]));')
    assert result==[True,False]

@pytest.mark.parametrize('field,value',(
    ('alpha_version','v33'),('alpha_first_enrolled_version','v19'),('alpha_enrolled',False),
    ('checked_use',False),('stable_member',True),('new_theorem_count',11),
    ('bounded_solution_bijection_proved',False),('zero_modulus_explicit',False),
    ('modulus_one_explicit',False),('fermat_all_inputs_proved',False)))
def test_congruence_javascript_guard_rejects_each_wrong_boundary(formatting,field,value):
    original=_goal(formatting.campaign,'G012');bad=deepcopy(original)
    bad['congruence_classification_progress'][field]=value
    result=_node(_function(formatting.html.decode(),'currentCongruenceProgress')+'\n'+
        'process.stdout.write(JSON.stringify(['+'currentCongruenceProgress('+json.dumps(original)+'),'+
        'currentCongruenceProgress('+json.dumps(bad)+')]));')
    assert result==[True,False]

def _notation_navigation(source,campaign,pathname):
    functions='\n'.join(_function(source,n) for n in ('currentPolynomialDivisionProgress',
        'currentPolynomialGcdProgress','renderNodeNotation','explorerBase','proofHref'))
    program='''
var window={location:{pathname:__PATH__}};
var state={campaign:__CAMPAIGN__,nodeDefinitions:new Map()};
function element(tag,label,attrs){return {tag:tag,label:label,attrs:attrs||{},children:[],appendChild:function(x){this.children.push(x);}};}
function empty(node){node.children=[];}
var ui={notationSection:{hidden:true},notation:element("ul")};
function applyAtlasRoute(){throw Error("No invented blueprint alias");}
__FUNCTIONS__
renderNodeNotation(state.campaign.nodes.find(x=>x.id==="G091"));
process.stdout.write(JSON.stringify({hidden:ui.notationSection.hidden,
 links:ui.notation.children.map(x=>x.children[0]),old:explorerBase("quadratic-reciprocity")}));
'''.replace('__PATH__',json.dumps(pathname)).replace('__CAMPAIGN__',json.dumps(campaign)).replace('__FUNCTIONS__',functions)
    return _node(program)

@pytest.mark.parametrize('path,gcd_prefix,old_prefix',(
    ('/proofs/grand-campaign/','../polynomial-gcd-bezout/explorer/defined/','../polynomial-euclidean-division/explorer/defined/'),
    ('/book/_static/constructive-research-campaign-v34/index.html',
     '../constructive-gcd-congruence-explorer-v34/polynomial-gcd-bezout/explorer/defined/',
     '../constructive-polynomial-euclidean-explorer-v34/polynomial-euclidean-division/explorer/defined/')))
def test_new_ten_and_old_seven_notation_routes_keep_correct_relative_depth(formatting,path,gcd_prefix,old_prefix):
    observed=_notation_navigation(formatting.html.decode(),formatting.campaign,path)
    assert observed['hidden'] is False and len(observed['links'])==17
    for row,identifier in zip(observed['links'][:7],OLD_DIVISION_IDS,strict=True):
        assert row['attrs']['href']==old_prefix+'definition/'+identifier+'.html?v='+'a'*12
    for row,(identifier,name) in zip(observed['links'][7:],DEFINITIONS.items(),strict=True):
        assert row['tag']=='a' and row['label']=='Reviewed conservative definition (notation only): '+name
        assert row['attrs']['href']==gcd_prefix+'definition/'+identifier+'.html?v='+'a'*12

def test_inline_javascript_compiles_and_historical_guards_are_identical(formatting):
    source=formatting.html.decode();parent=formatting.parents['index.html'].decode()
    scripts=[body for attrs,body in re.findall(r'<script\b([^>]*)>(.*?)</script>',source,re.S)
             if 'type="application/json"' not in attrs]
    subprocess.run(['node','-e','const vm=require("node:vm");JSON.parse(require("node:fs").readFileSync(0,"utf8")).forEach(x=>new vm.Script(x));'],
        input=json.dumps(scripts),text=True,capture_output=True,check=True,timeout=20)
    for name in ('currentResearchAdmitted','currentPolynomialDivisionProgress','proved'):
        assert _function(source,name)==_function(parent,name)
    assert 'first admitted to Alpha v32, not Stable' in source
    assert 'Alpha v33 general division and representation laws' in source
    assert 'Alpha v34 normalized polynomial gcd/Bézout proved' in source
    assert 'Alpha v34 exact congruence classes and bounded solutions' in source
    embedded=re.search(r'<script type="application/json" id="campaign-data">(.*?)</script>',source,re.S)
    assert embedded and json.loads(embedded[1])==formatting.campaign

@pytest.mark.parametrize('value',(None,{},SimpleNamespace(catalog={},proofs_verified=True)))
def test_forged_capability_cannot_publish_or_use_strict_assertion_wrapper(value):
    with pytest.raises(atlas.publication.PublicationError):atlas.build_files_from_live(value)
    with pytest.raises(atlas.publication.PublicationError):_assert_published_files(value,{})

def test_private_display_fixture_never_authorizes_release(formatting):
    assert formatting.fixture_notice==NOTICE
    with pytest.raises(atlas.publication.PublicationError):atlas.build_files_from_live(formatting)

@pytest.mark.parametrize('revision',('',None,'A'*12,'a'*11,'a'*13,'../foreign'))
def test_bad_revision_cannot_render(formatting,revision):
    with pytest.raises(atlas.publication.PublicationError):
        atlas._html(formatting.parents['index.html'].decode(),formatting.campaign,formatting.graph,formatting.routes,revision)

@pytest.mark.parametrize('attack',('old_definition','old_dependency','new_id','blueprint','override'))
def test_definition_projection_rejects_old_identity_changes(formatting,monkeypatch,attack):
    bad=deepcopy(formatting.graph)
    if attack=='old_definition':bad['reviewed_definitions'][0]['name']='foreign'
    elif attack=='old_dependency':
        bad['reviewed_definitions'][0]['dependencies']=['foreign_unproved_dependency']
        assert bad['reviewed_definitions'][0]!=formatting.graph['reviewed_definitions'][0]
    elif attack=='new_id':bad['reviewed_definitions'][-1]['id']='ND9999'
    elif attack=='blueprint':bad['definitions']=[]
    else:bad['reviewed_definition_edge_count']=885
    monkeypatch.setattr(atlas,'build_definition_graph',lambda _:bad)
    with pytest.raises(atlas.publication.PublicationError):atlas._graph(formatting.old_graph,formatting.campaign,formatting.routes)

@pytest.mark.parametrize('attack',('short','duplicate','foreign_package','foreign_slug','wrong_partition'))
def test_family_route_map_exact68_and_five_reader_partitions(formatting,attack):
    metadata=deepcopy(atlas.publication._all_family_metadata())
    if attack=='short':metadata=metadata[:-1]
    elif attack=='duplicate':metadata=(*metadata[:-1],metadata[0])
    elif attack=='foreign_package':metadata[0]['package']='foreign'
    elif attack=='foreign_slug':metadata[0]['slug']='../foreign'
    else:metadata[0]['package']=atlas.publication.OUTPUT_NAMES['gcd-congruence']
    with pytest.raises(atlas.publication.PublicationError):atlas._package_map(metadata)

@pytest.mark.parametrize('attack',('old_status','old_evidence','g091_closed','lost_division','lost_euclidean','lost_provenance','lost_gcd','old_source'))
def test_preservation_guard_rejects_changed_history(formatting,attack):
    bad=deepcopy(formatting.campaign)
    if attack=='old_status':_goal(bad,'G009')['status']='open'
    elif attack=='old_evidence':_goal(bad,'G012')['evidence']['alpha_version']='v34'
    elif attack=='g091_closed':_goal(bad,'G091')['status']='available'
    elif attack=='lost_division':_goal(bad,'G091')['polynomial_prerequisite_progress']={}
    elif attack=='lost_euclidean':_goal(bad,'G091')['polynomial_euclidean_progress']={}
    elif attack=='lost_provenance':_goal(bad,'G091')['historical_v32_polynomial_progress']={}
    elif attack=='lost_gcd':_goal(bad,'G091')['polynomial_gcd_progress']['full_G091_proved']=True
    else:bad['sources'][0]['path']='foreign'
    with pytest.raises(atlas.publication.PublicationError):atlas._preserved(formatting.original,bad)

@pytest.mark.parametrize('attack',('statement','hash','node_map','row_node','not_checked','first_version','bundle','principal'))
def test_admission_projection_rejects_substituted_actual_row_boundaries(formatting,attack):
    family=atlas.research.FAMILIES[1];report=deepcopy(formatting.reports[family.slug])
    by_name={r['name']:deepcopy(r) for r in formatting.catalog['theorems']}
    name=family.owned_names[0];row=by_name[name]
    if attack=='statement':row['statement']='0=1'
    elif attack=='hash':report['rows'][0]['statement_sha256']='f'*64
    elif attack=='node_map':report['owned_node_ids'][name]=0
    elif attack=='row_node':report['rows'][0]['node_id']=0
    elif attack=='not_checked':row['checked_use']=False
    elif attack=='first_version':row['alpha_v34_frontier_enrollment']['first_enrolled_version']='v33'
    elif attack=='bundle':report['bundle']['sha256']='f'*64
    else:report['principal_roots'][0]['complete_ordinary_ha_checked']=False
    with pytest.raises(atlas.publication.PublicationError):atlas._admitted_family(family,report,by_name)

def test_live_guard_is_first_and_last_and_projection_never_mints_authority():
    tree=ast.parse(inspect.getsource(atlas.build_files_from_live)).body[0]
    assert ast.unparse(tree.body[0])=='publication.require_live(context)'
    assert ast.unparse(tree.body[-2])=='publication.require_live(context)'
    assert ast.unparse(tree.body[-1])=='return files'
    assert 'FreshProofAudit(' not in inspect.getsource(atlas)

def _assert_published_content(context,files):
    """Pure assertions consumed by the genuine six-phase publication harness."""
    assert set(files)=={'campaign.json','definitions.json','dag-audit.json','index.html'}
    assert all(type(k) is str and type(v) is bytes for k,v in files.items())
    parents=atlas.parent_files();old,old_graph,old_audit=atlas._parent(parents)
    campaign,graph,audit=(atlas.publication.strict_json(files[n]) for n in ('campaign.json','definitions.json','dag-audit.json'))
    _assert_preservation(old,campaign)
    assert campaign['meta']['current_alpha_version']=='v34'
    assert campaign['meta']['current_alpha_checked_use_count']==4223
    assert campaign['meta']['current_alpha_catalog_sha256']==context.catalog_sha256
    assert campaign['meta']['historical_alpha_versions']==[*old['meta']['historical_alpha_versions'],'v33']
    assert campaign['meta']['current_G091_proved'] is False
    gcd=_goal(campaign,'G091')['polynomial_gcd_progress']
    congruence=_goal(campaign,'G012')['congruence_classification_progress']
    for progress,count,slug,nodes,edges,flags in ((gcd,119,atlas.SLUGS[0],493,1578,GCD_FLAGS),
                                                (congruence,12,atlas.SLUGS[1],215,647,CONGRUENCE_FLAGS)):
        report=_thaw(context.families[slug])
        assert progress['alpha_version']==progress['alpha_first_enrolled_version']=='v34'
        assert progress['checked_use'] is progress['alpha_enrolled'] is True and progress['stable_member'] is False
        assert progress['new_theorem_count']==count and all(progress[k] is True for k in flags)
        assert progress['bundle']==report['bundle'] and progress['principal_roots']==report['principal_roots']
        assert progress['bundle']['nodes_including_packaging_root']==nodes
        assert progress['bundle']['dependency_edges_including_packaging']==edges
        family=atlas.research.research_family(slug)
        assert progress['bundle']['sha256']==family.artifact_sha256
        assert tuple(r['name'] for r in progress['principal_roots'])==family.principal_roots
        assert len(progress['proof_routes'])==len(family.principal_roots)
        assert progress['current_catalog_sha256']==context.catalog_sha256
        assert progress['current_source_binding_sha256']==context.source_binding_sha256
    assert gcd['full_G091_proved'] is gcd['arbitrary_identity_pair_quotient_uniqueness_proved'] is False
    assert gcd['conservative_definition_ids']==list(DEFINITIONS)
    assert len(campaign['current_proof_family_packages'])==68
    assert campaign['current_proof_family_packages']==atlas._package_map(atlas.publication._all_family_metadata())
    assert audit['current_research_admission']['ordinary_principal_count']==19
    assert audit['historical_parent_audit']['record']==old_audit
    old_defs={r['id']:r for r in old_graph['reviewed_definitions']};new_defs={r['id']:r for r in graph['reviewed_definitions']}
    assert len(new_defs)==407 and {k:new_defs[k] for k in old_defs}==old_defs
    assert {k:new_defs[k]['name'] for k in set(new_defs)-set(old_defs)}==DEFINITIONS
    assert graph['reviewed_definition_edge_count']==884
    catalog=context.catalog if type(context.catalog) is dict else _thaw(context.catalog)
    checked=validate_campaign_dags(campaign,definition_graph=graph,catalog=catalog,catalog_sha256=context.catalog_sha256)
    assert (checked.theorem_count,checked.theorem_edge_count,checked.milestone_count)==(4223,13816,144)
    assert checked.milestone_dag_sha256==old_audit['milestone_dag_sha256']
    source=files['index.html'].decode()
    embedded=re.search(r'<script type="application/json" id="campaign-data">(.*?)</script>',source,re.S)
    assert embedded and json.loads(embedded[1])==campaign
    for path in ('/proofs/grand-campaign/','/book/_static/constructive-research-campaign-v34/index.html'):
        result=_notation_navigation(source,campaign,path)
        assert result['hidden'] is False and len(result['links'])==17
        assert all('v='+context.revision in r['attrs']['href'] for r in result['links'])
    assert atlas.parent_files()==parents

def _assert_published_files(context,files):
    atlas.publication.require_live(context)
    _assert_published_content(context,files)
    atlas.publication.require_live(context)
