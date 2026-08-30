"""Independent prerequisite-atlas tests; formatter fixtures are NOT proofs.

Pure fixtures below use the actual immutable parent atlas but deliberately
non-authorizing display records. They call only private formatters, never a
successful proof verifier or the verified-reader entrypoint. The two helpers
at the bottom accept only the reader test's genuinely supplied same-live
state, selection, corpus and report. No receipt is loaded as proof authority.
"""

from __future__ import annotations

from copy import deepcopy
from dataclasses import fields, is_dataclass, replace
from hashlib import sha256
import inspect
import json
from pathlib import Path
import re
import subprocess
import sys
from types import SimpleNamespace

import pytest


def _authority_modules():
    return {name:module for name,module in sys.modules.items()
            if name=='peano_lab.library.editions_v31' or name.startswith('peano_lab.library.editions_v31.')}


_BEFORE_IMPORT=_authority_modules()
import extend_constructive_polynomial_division_campaign as campaign
import constructive_polynomial_division_definitions as definitions
from constructive_formula_compactor import _LocalDefinedParser
from peano_lab.kernel.formulas import parse_formula_with_names
from sync_constructive_grand_campaign import _definition_dags, _milestone_dag, CampaignDagError
assert _authority_modules()==_BEFORE_IMPORT


NOTICE='FORMATTER FIXTURE ONLY: NOT PROOF EVIDENCE, NOT A VERIFIED RELEASE'
EXPECTED_PARENT_PINS={
    'campaign.json':(623714,'5dd8a6c97f33643fbd030ab9420f9507069cd0e57c573152c2f65766522cb788'),
    'definitions.json':(1455910,'231c5974c698c62185f29c26e2ce35c447b61f14bd611932400b574c32748085'),
    'dag-audit.json':(1581,'5ea16177f405e482c69a846f3f04b9a8fc71e60d5933d4e57b0e6e4e39d62fbb'),
    'index.html':(683902,'604adbf407fb250fefbe33ed8badd8a6026fdba5207978d4509a54368982ea48'),
}
EXPECTED_DEFINITIONS=(
    ('ND0327','FpCoefficientNegation'),('ND0328','FpCoefficientSubtraction'),
    ('ND0329','PolynomialSuffix'),('ND0330','FpPolynomialTrim'),
    ('ND0331','FpMonic'),('ND0332','FpMonicNormalization'),('ND0333','FpSyntheticDivision'),
)
EXPECTED_ROOTS=(
    'prime_field_polynomial_subtract_exists',
    'prime_field_polynomial_trim_exists_unique',
    'prime_field_polynomial_monic_normalization_exists_unique',
    'prime_field_polynomial_synthetic_exists_unique',
    'prime_field_polynomial_synthetic_represented_degree',
    'prime_field_polynomial_synthetic_zero_remainder_iff',
)
META_ADDITIONS={'polynomial_prerequisite_new_theorem_count','polynomial_prerequisite_complete_cone_count',
    'polynomial_prerequisite_alpha_admission','polynomial_prerequisite_G091_closed',
    'polynomial_prerequisite_release_date'}
UNTOUCHED_AUDIT=('alpha_version','catalog_sha256','theorem_count','theorem_edge_count','theorem_dag_sha256',
    'milestone_count','milestone_proof_edge_count','milestone_dag_sha256','research_proof_dag')


@pytest.fixture(autouse=True)
def no_authority_imports():
    before=_authority_modules()
    yield
    after=_authority_modules()
    assert before.keys()==after.keys()
    assert all(after[name] is module for name,module in before.items())


@pytest.fixture(scope='module')
def formatting():
    parents=campaign.parent_files()
    original,parent_graph,parent_audit=campaign._parent_context(parents)
    before=campaign._json(original)
    state=campaign.support.load_candidate_state(final=True)
    tags={row.name:f'PQ{index:04X}' for index,row in enumerate(state.rows,1)}
    corpus={'family_title':NOTICE,'tags':tags,'root_names':list(EXPECTED_ROOTS),'fixture_notice':NOTICE}
    spec=next(row for row in state.rows if row.name==EXPECTED_ROOTS[-1])
    root={'name':spec.name,'id':tags[spec.name],'statement_sha256':sha256(spec.statement.encode()).hexdigest(),
          'fixture_notice':NOTICE}
    pin=SimpleNamespace(path='FORMATTER_ONLY_NOT_A_PROOF.json',sha256='f'*64,nodes=293,edges=1)
    report={'principal_roots':[{'name':name,'fixture_notice':NOTICE} for name in EXPECTED_ROOTS],
            'fixture_notice':NOTICE}
    selection=SimpleNamespace(plan=SimpleNamespace(ordered_names_sha256='FORMATTER_ONLY',dependency_edge_count=1),
                              fixture_notice=NOTICE)
    projected=campaign._project(original,corpus,root,pin,report)
    graph=campaign.build_definition_graph(projected)
    audit=campaign._audit(original,parent_graph,parent_audit,projected,graph,selection,pin)
    html=campaign._html(parents['index.html'].decode(),projected,graph)
    assert campaign._json(original)==before and campaign.parent_files()==parents
    return SimpleNamespace(parents=parents,original=original,parent_graph=parent_graph,parent_audit=parent_audit,
        corpus=corpus,root=root,pin=pin,report=report,state=state,selection=selection,
        projected=projected,graph=graph,audit=audit,html=html,fixture_notice=NOTICE)


def _goal(document,identifier='G091'):
    return next(row for row in document['nodes'] if row['id']==identifier)


def _same_ast(first,second):
    pending,seen=[(first,second)],set()
    while pending:
        left,right=pending.pop()
        assert type(left) is type(right)
        if (id(left),id(right)) in seen:
            continue
        seen.add((id(left),id(right)))
        if is_dataclass(left):
            pending.extend((getattr(left,field.name),getattr(right,field.name)) for field in fields(left))
        else:
            assert left==right


@pytest.mark.parametrize('name',tuple(EXPECTED_PARENT_PINS))
def test_actual_four_file_parent_has_literal_independent_byte_identity(name):
    raw=campaign.parent_files()[name]
    assert (len(raw),sha256(raw).hexdigest())==EXPECTED_PARENT_PINS[name]
    assert campaign.PARENT_PINS[name]==dict(zip(('bytes','sha256'),EXPECTED_PARENT_PINS[name]))


def test_every_unrelated_node_and_all_120_goal_statuses_are_exactly_preserved(formatting):
    old={row['id']:row for row in formatting.original['nodes']}
    new={row['id']:row for row in formatting.projected['nodes']}
    assert len(old)==len(new)==144 and old.keys()==new.keys()
    assert [r['id'] for r in formatting.projected['nodes']]==[r['id'] for r in formatting.original['nodes']]
    assert all(row==old[identifier] for identifier,row in new.items() if identifier!='G091')
    goals=[identifier for identifier in old if identifier.startswith('G')]
    assert len(goals)==120
    assert {identifier:new[identifier]['status'] for identifier in goals}=={identifier:old[identifier]['status'] for identifier in goals}
    assert all(new[name]['statement']==old[name]['statement'] and new[name]['deps']==old[name]['deps']
               and new[name].get('evidence')==old[name].get('evidence') for name in old)


def test_g009_full_research_completion_and_every_old_release_boundary_remain_identical(formatting):
    assert _goal(formatting.projected,'G009')==_goal(formatting.original,'G009')
    g009=_goal(formatting.projected,'G009')
    assert g009['status']=='available' and g009['research_proof_closed'] is True
    assert g009['evidence']['full_G009_finite_coded_contract_proved'] is True
    assert all(formatting.projected['ambitious_boundaries'][name]==value
               for name,value in formatting.original['ambitious_boundaries'].items())
    assert {key:value for key,value in formatting.projected['meta'].items() if key not in META_ADDITIONS}==formatting.original['meta']


@pytest.mark.parametrize('field',('status','statement','deps','family','layer','difficulty','title'))
def test_g091_keeps_its_full_unproved_contract_and_original_proof_dependencies(formatting,field):
    assert _goal(formatting.projected)[field]==_goal(formatting.original)[field]
    assert _goal(formatting.projected)['status']=='open'
    assert 'evidence' not in _goal(formatting.original)
    assert 'evidence' not in _goal(formatting.projected)


@pytest.mark.parametrize('key',('full_G091_proved','alpha_enrolled','checked_use','stable_member'))
def test_prerequisite_record_never_claims_full_goal_or_admission(formatting,key):
    assert _goal(formatting.projected)['polynomial_prerequisite_progress'][key] is False


@pytest.mark.parametrize('key,expected',(('new_theorem_count',85),('inherited_alpha_theorem_count',207),
    ('complete_cone_theorem_count',292),('ordinary_principal_count',6),('domain','D04'),('family','F10')))
def test_prerequisite_counts_and_domain_do_not_double_count_inherited_alpha(formatting,key,expected):
    assert _goal(formatting.projected)['polynomial_prerequisite_progress'][key]==expected


def test_all_six_real_specification_routes_are_polynomial_prerequisites_not_a_g091_root(formatting):
    progress=_goal(formatting.projected)['polynomial_prerequisite_progress']
    assert tuple(campaign.checkpoints.PRINCIPAL_ROOTS)==EXPECTED_ROOTS
    assert [row['label'] for row in progress['proof_routes']]==list(EXPECTED_ROOTS)
    assert [row['tag'] for row in progress['proof_routes']]==[formatting.corpus['tags'][name] for name in EXPECTED_ROOTS]
    assert all(row['route']=='polynomial-division-prerequisites' for row in progress['proof_routes'])
    assert progress['representative_proof_tag']=='PQ0055'
    chapter=_goal(formatting.projected)['additional_checked_chapters'][-1]
    assert chapter['closes_full_milestone'] is chapter['full_G091_proved'] is False
    assert chapter['alpha_checked_use'] is chapter['stable_member'] is False
    assert chapter['proof_routes']==progress['proof_routes']
    assert _goal(formatting.projected)['additional_checked_chapters'][:-1]==_goal(formatting.original)['additional_checked_chapters']


@pytest.mark.parametrize('phrase',('Arbitrary-divisor','polynomial gcd','Irreducible polynomials','quotient-field'))
def test_remaining_g091_obligations_are_explicit_and_not_inferred_from_prerequisites(formatting,phrase):
    progress=_goal(formatting.projected)['polynomial_prerequisite_progress']
    assert any(phrase in text for text in progress['remaining_obligations'])
    assert 'G091 remains open' in progress['summary']


@pytest.mark.parametrize('identifier,name',EXPECTED_DEFINITIONS)
def test_seven_new_definition_records_round_trip_to_the_exact_independent_expansions(formatting,identifier,name):
    item=definitions.ALL_CONSTRUCTIVE_DEFINITIONS_BY_NAME[name]
    record=formatting.projected['definitions'][name]
    assert item.stable_id==identifier==record['reviewed_definition_id']
    assert record['parameters']==list(item.parameters)
    assert record['reviewed_expansion_sha256']==sha256(item.template_source.encode()).hexdigest()
    assert record['exact_defined_expansion_equivalence_checked'] is True
    aliases={**definitions.ALL_CONSTRUCTIVE_DEFINITIONS_BY_NAME,
             'BetaSum':replace(definitions.ALL_CONSTRUCTIVE_DEFINITIONS_BY_NAME['Sum'],name='BetaSum')}
    exact,free=parse_formula_with_names(item.template_source)
    parser=_LocalDefinedParser(record['expansion'],aliases)
    parser.free=list(free)
    _same_ast(parser.parse(),exact)
    assert tuple(parser.free)==free


def test_all_old_blueprint_and_reviewed_identities_remain_unchanged(formatting):
    assert len(formatting.projected['definitions'])==len(formatting.original['definitions'])+7==474
    assert all(formatting.projected['definitions'][name]==row for name,row in formatting.original['definitions'].items())
    prior={row['id']:row for row in formatting.parent_graph['reviewed_definitions']}
    current={row['id']:row for row in formatting.graph['reviewed_definitions']}
    assert len(prior)==383 and len(current)==390
    assert all(current[name]==row for name,row in prior.items())
    assert set(current)-set(prior)=={identifier for identifier,_ in EXPECTED_DEFINITIONS}
    assert 'Multiplicative' not in formatting.original['definitions']
    assert 'Multiplicative' not in formatting.projected['definitions']
    assert formatting.projected['definitions']['MultiplicativePrefix']==formatting.original['definitions']['MultiplicativePrefix']
    assert formatting.projected['definitions']['MultiplicativePrefix']['parameters']==['N','F']


def test_three_graph_categories_and_actual_topological_layers_stay_separate(formatting):
    graph=formatting.graph
    assert (graph['reviewed_definition_count'],graph['reviewed_definition_edge_count'])==(390,844)
    assert max(row['topological_layer'] for row in graph['reviewed_definitions'])==12
    _definition_dags(formatting.projected,graph)
    first,old_edges=_milestone_dag(formatting.original)
    second,new_edges=_milestone_dag(formatting.projected)
    assert second==first and new_edges==old_edges==313
    assert {row['kind'] for row in graph['definition_edges']}=={'definition_uses_definition'}
    assert {row['kind'] for row in graph['milestone_usage_edges']}=={'statement_uses_definition','declared_notation'}
    assert all(row['source']=='G091' and row['kind']=='declared_notation'
               for row in graph['milestone_usage_edges'] if row['target'] in {name for _,name in EXPECTED_DEFINITIONS})


@pytest.mark.parametrize('key',UNTOUCHED_AUDIT)
def test_old_alpha_and_g009_proof_dag_records_are_preserved_not_freshly_replayed(formatting,key):
    assert formatting.audit[key]==formatting.parent_audit[key]


def test_audit_explains_inherited_authority_and_separate_actual_prerequisite_cone(formatting):
    boundary=formatting.audit['inherited_proof_dag_boundary']
    assert boundary['alpha_proof_dag_recomputed_here'] is boundary['G009_proof_dag_recomputed_here'] is False
    assert boundary['saved_parent_audit_is_new_proof_authority'] is False
    assert boundary['literal_parent_proof_records_preserved'] is boundary['current_milestone_and_definition_dags_recomputed'] is True
    assert (boundary['bytes'],boundary['sha256'])==EXPECTED_PARENT_PINS['dag-audit.json']
    separate=formatting.audit['polynomial_prerequisite_proof_dag']
    assert (separate['theorem_count'],separate['new_theorem_count'],separate['inherited_alpha_theorem_count'])==(292,85,207)
    assert separate['full_G091_proved'] is separate['alpha_admission_performed'] is separate['stable_admission_performed'] is False
    assert separate['notation_edges_are_proof_premises'] is False
    assert separate['ordered_names_sha256']==formatting.selection.plan.ordered_names_sha256


@pytest.mark.parametrize('index,identifier,ending',(
    (0,'S85','FORMATTER_ONLY_NOT_A_PROOF.json'),
    (1,'S86','book/_static/constructive-polynomial-division-explorer/proof-audit.json'),
    (2,'S87','research/arithmetic-library/prime-field-polynomial-division-prerequisites-rfc-v1.md'),
    (3,'S88','book/_static/constructive-g009-explorer/grand-campaign/campaign.json'),
))
def test_provenance_sources_are_additive_distinct_and_use_actual_reader_layout(formatting,index,identifier,ending):
    old=formatting.original['sources']
    assert formatting.projected['sources'][:len(old)]==old
    added=formatting.projected['sources'][len(old):]
    assert len(added)==4
    assert added[index]['id']==identifier and added[index]['path']==ending
    assert len({row['id'] for row in formatting.projected['sources']})==len(old)+4


def _function(html,name):
    match=re.search(r'      function '+re.escape(name)+r'\([^\n]*\) \{.*?\n      \}',html,flags=re.S)
    assert match,name
    return match[0]


def _node(source):
    run=subprocess.run(['node'],input=source,capture_output=True,text=True,timeout=20)
    assert run.returncode==0,run.stderr[-12000:]
    return json.loads(run.stdout)


ROUTES=('polynomial-division-prerequisites','multiplicative-convolution','quadratic-reciprocity',
        'bertrand-postulate','dirichlet-inverses','prime-fields','polynomial-products')


@pytest.mark.parametrize('deployed',(False,True),ids=('raw','public'))
@pytest.mark.parametrize('route',ROUTES)
def test_actual_route_function_preserves_old_siblings_and_new_same_package(formatting,deployed,route):
    html=formatting.html.decode()
    path='/proofs/grand-campaign/index.html' if deployed else '/book/_static/constructive-polynomial-division-explorer/grand-campaign/index.html'
    source='const window={location:{pathname:'+json.dumps(path)+'}};\n'+_function(html,'explorerBase')
    value=_node(source+'\nconsole.log(JSON.stringify(explorerBase('+json.dumps(route)+')));')
    if deployed or route=='polynomial-division-prerequisites':
        expected='../'+route+'/explorer/defined/'
    else:
        package=('constructive-g009-explorer' if route=='multiplicative-convolution' else
                 'constructive-historical-explorers-v31' if route in ('quadratic-reciprocity','bertrand-postulate')
                 else 'constructive-completed-lower-explorer-v31')
        expected='../../'+package+'/'+route+'/explorer/defined/'
    assert value==expected


def test_header_links_and_g009_proof_guard_stay_literal_while_g091_stays_open(formatting):
    old=formatting.parents['index.html'].decode()
    html=formatting.html.decode()
    for name in ('localResearchProved','proved','describeStatus'):
        assert _function(html,name)==_function(old,name)
    before=re.search(r'      var PROOF_ROOTS = \{.*?\n      \};',old,flags=re.S)
    after=re.search(r'      var PROOF_ROOTS = \{.*?\n      \};',html,flags=re.S)
    assert before and after and before[0]==after[0]
    assert not re.search(r'^\s*G091:',html,flags=re.M)
    for key in ('data-proof-home','data-proof-quadratic','data-proof-bertrand'):
        assert re.search(r'<a href="[^"]+" '+key+r'>',html)[0]==re.search(r'<a href="[^"]+" '+key+r'>',old)[0]
    source='\n'.join(_function(html,name) for name in ('localResearchProved','proved','describeStatus','statusCaveat'))
    source+='\nconst g009='+json.dumps(_goal(formatting.projected,'G009'))+';'
    source+='\nconst g091='+json.dumps(_goal(formatting.projected))+';'
    source+='\nconsole.log(JSON.stringify({old:proved(g009),now:proved(g091),status:describeStatus(g091),caveat:statusCaveat(g091)}));'
    result=_node(source)
    assert result['old'] is True and result['now'] is False
    assert result['status']=='Open research objective' and 'G091 remains open' in result['caveat']


def test_embedded_campaign_and_initial_qr_structure_are_preserved(formatting):
    html=formatting.html.decode()
    match=re.search(r'<script type="application/json" id="campaign-data">(.*?)</script>',html,flags=re.S)
    assert match and json.loads(match[1])==formatting.projected
    for token in ('data-proof-home','data-proof-quadratic','data-proof-bertrand','data-node-proof-links',
                  'data-node-status','data-node-statement','data-definition-domain','data-graph-svg'):
        # Preserve only controls that actually exist in the frozen parent.
        if token in formatting.parents['index.html'].decode():
            assert token in html
    assert 'Verified polynomial prerequisite — G091 remains open; not Alpha/Stable' in html
    assert 'PQ0055' in html and 'MX0059' in html


@pytest.mark.parametrize('attack',('schema','alpha_count','goal_count','node_count','g009_open','g009_full_false',
    'g091_closed','g091_family','catalog','stable_count','definition_count','audit_theorems','audit_theorems_float',
    'audit_snapshot','graph_count','graph_usage_kind'))
def test_actual_parent_metadata_mutations_fail_closed_without_loading_alpha(formatting,attack):
    original,graph,audit=deepcopy(formatting.original),deepcopy(formatting.parent_graph),deepcopy(formatting.parent_audit)
    if attack=='schema': original['schema']='other'
    elif attack=='alpha_count': original['meta']['current_alpha_checked_use_count']=3797
    elif attack=='goal_count': original['meta']['goal_count']=121
    elif attack=='node_count': original['nodes'].pop()
    elif attack=='g009_open': _goal(original,'G009')['status']='open'
    elif attack=='g009_full_false': _goal(original,'G009')['evidence']['full_G009_finite_coded_contract_proved']=False
    elif attack=='g091_closed': _goal(original)['status']='available'
    elif attack=='g091_family': _goal(original)['family']='F01'
    elif attack=='catalog': original['ambitious_boundaries']['alpha_v31_edition']['catalog_sha256']='0'*64
    elif attack=='stable_count': original['ambitious_boundaries']['alpha_v31_edition']['stable_closed_count']=433
    elif attack=='definition_count': original['definitions'].pop(next(iter(original['definitions'])))
    elif attack=='audit_theorems': audit['theorem_count']=3797
    elif attack=='audit_theorems_float': audit['theorem_count']=3796.0
    elif attack=='audit_snapshot': audit['campaign_snapshot_sha256']='0'*64
    elif attack=='graph_count': graph['definition_count']-=1
    elif attack=='graph_usage_kind': graph['milestone_usage_edges'][0]['kind']='proof_dependency'
    parents={**formatting.parents,'campaign.json':campaign._json(original),
             'definitions.json':campaign._json(graph),'dag-audit.json':campaign._json(audit)}
    with pytest.raises((campaign.support.PolynomialDivisionError,CampaignDagError)):
        campaign._parent_context(parents)


@pytest.mark.parametrize('attack',('definition_shadow','source_collision','existing_progress','closed_g091','open_g009',
    'metadata_collision','boundary_collision'))
def test_pure_projection_refuses_shadowed_records_and_false_goal_transitions(formatting,attack):
    original=deepcopy(formatting.original)
    if attack=='definition_shadow': original['definitions']['FpMonic']={'expansion':'0=0'}
    elif attack=='source_collision': original['sources'].append({'id':'S85'})
    elif attack=='existing_progress': _goal(original)['polynomial_prerequisite_progress']={}
    elif attack=='closed_g091': _goal(original)['status']='available'
    elif attack=='open_g009': _goal(original,'G009')['status']='open'
    elif attack=='metadata_collision': original['meta']['polynomial_prerequisite_new_theorem_count']=85
    elif attack=='boundary_collision': original['ambitious_boundaries']['g091_polynomial_prerequisite_progress']={}
    with pytest.raises(campaign.support.PolynomialDivisionError):
        campaign._project(original,formatting.corpus,formatting.root,formatting.pin,formatting.report)


@pytest.mark.parametrize('attack',('reviewed_count','reviewed_edge_count','old_route','old_expansion','usage_kind',
    'usage_target','definition_cycle','milestone_edge'))
def test_separate_dag_validation_rejects_cross_graph_or_inherited_mutations(formatting,attack):
    projected,graph=deepcopy(formatting.projected),deepcopy(formatting.graph)
    if attack=='reviewed_count': graph['reviewed_definition_count']-=1
    elif attack=='reviewed_edge_count': graph['reviewed_definition_edge_count']+=1
    elif attack=='old_route': graph['reviewed_definitions'][0]['route']='polynomial-division-prerequisites'
    elif attack=='old_expansion':
        name=next(iter(formatting.original['definitions']))
        projected['definitions'][name]['meaning']='changed old meaning'
        graph=campaign.build_definition_graph(projected)
    elif attack=='usage_kind': graph['milestone_usage_edges'][0]['kind']='proof_dependency'
    elif attack=='usage_target': graph['milestone_usage_edges'][0]['target']='PQ0055'
    elif attack=='definition_cycle':
        graph['reviewed_definitions'][0]['dependencies']=[graph['reviewed_definitions'][0]['name']]
    elif attack=='milestone_edge': _goal(projected)['deps'].append('G091')
    with pytest.raises((campaign.support.PolynomialDivisionError,CampaignDagError)):
        campaign._audit(formatting.original,formatting.parent_graph,formatting.parent_audit,
                        projected,graph,formatting.selection,formatting.pin)


@pytest.mark.parametrize('attack',('dispatcher','duplicate_dispatcher','new_route_collision','old_shortcut','definition_table','proof_root','script_injection'))
def test_navigation_and_embedding_mutations_are_rejected(formatting,attack):
    source=formatting.parents['index.html'].decode()
    projected=deepcopy(formatting.projected)
    if attack=='dispatcher': source=source.replace('        var currentFamilies = ','        var changedFamilies = ',1)
    elif attack=='duplicate_dispatcher': source+='\n        var currentFamilies = {};\n'
    elif attack=='new_route_collision': source=source.replace('        var currentFamilies = {','        var currentFamilies = {"polynomial-division-prerequisites":"other",',1)
    elif attack=='old_shortcut': source=source.replace('if (route === "multiplicative-convolution")','if (route === "foreign")',1)
    elif attack=='definition_table': source=source.replace('      var COMPILED_DEFINITIONS = {','      var NOT_COMPILED_DEFINITIONS = {',1)
    elif attack=='proof_root': source=source.replace('      var PROOF_ROOTS = {\n','      var PROOF_ROOTS = {\n        G091: {route:"foreign"},\n',1)
    elif attack=='script_injection': projected['title']='</script><script>alert(1)</script>'
    with pytest.raises(campaign.support.PolynomialDivisionError):
        campaign._html(source,projected,formatting.graph)


@pytest.mark.parametrize('attack',('missing','extra','bool_bytes','oversize','wrong_sha','bad_sha_type'))
def test_parent_registration_is_literal_and_reject_only(monkeypatch,attack):
    pins=deepcopy(campaign.PARENT_PINS)
    if attack=='missing': pins.pop('campaign.json')
    elif attack=='extra': pins['extra.json']=deepcopy(pins['campaign.json'])
    elif attack=='bool_bytes': pins['campaign.json']['bytes']=True
    elif attack=='oversize': pins['campaign.json']['bytes']=campaign.MAX_CAMPAIGN_BYTES+1
    elif attack=='wrong_sha': pins['campaign.json']['sha256']='0'*64
    elif attack=='bad_sha_type': pins['campaign.json']['sha256']=None
    monkeypatch.setattr(campaign,'PARENT_PINS',pins)
    with pytest.raises(campaign.support.PolynomialDivisionError):
        campaign.parent_files()


@pytest.mark.parametrize('report',(None,{},[],{'schema':campaign.REPORT_SCHEMA},
    {'polynomial_prerequisite_principals_checked':True},
    {'schema':campaign.REPORT_SCHEMA,'fresh_worker_count':8,'published':False}))
def test_fake_or_incomplete_reports_do_not_enter_verified_display(report):
    with pytest.raises(campaign.support.PolynomialDivisionError):
        campaign._research_evidence({},report,None,None)


def test_formatter_fixture_is_rejected_by_real_guard_and_has_no_proof_capability(formatting):
    assert formatting.fixture_notice==NOTICE
    assert type(formatting.selection) is SimpleNamespace
    with pytest.raises(campaign.support.PolynomialDivisionError):
        campaign._research_evidence(formatting.corpus,formatting.report,formatting.state,formatting.selection)


def test_public_entrypoint_refuses_fabricated_empty_evidence_and_writes_nothing():
    before=campaign.parent_files()
    with pytest.raises(campaign.support.PolynomialDivisionError):
        campaign.build_files_for_verified_reader({}, {}, None, None)
    assert campaign.parent_files()==before


def test_source_binding_is_real_stable_metadata_only_and_uses_no_full_catalogue_loader(monkeypatch):
    observed=[]
    bounded_bytes=campaign.support.bounded_bytes
    def record_read(path,*args,**kwargs):
        observed.append(path)
        return bounded_bytes(path,*args,**kwargs)
    monkeypatch.setattr(campaign.support,'bounded_bytes',record_read)
    first=campaign.source_binding()
    assert re.fullmatch('[0-9a-f]{64}',first)
    assert campaign.source_binding()==first
    assert all(campaign.ROOT/f'peano-lab/py/peano_lab/library/{name}' in observed
               for name in ('bertrand_defined_edition.py','defined_edition.py','defined_syntax.py'))
    source=inspect.getsource(campaign)
    assert 'load_catalog' not in source
    assert 'verify_in_fresh_windows(' not in source
    assert 'verify_checkpoint(' not in source and 'verify_principal_root(' not in source
    assert 'write_bytes(' not in source and 'write_text(' not in source


ACTUAL_EVIDENCE_MUTATIONS=(
    'wrong_bundle_report','missing_ordinary','extra_ordinary','ordinary_order',
    'ordinary_statement','ordinary_count_zero','ordinary_count_bool','ordinary_count_overflow',
    'novelty_missing','novelty_duplicate','corpus_family','corpus_count','alpha_count',
    'enrolled_count','stable_count','corpus_bundle','missing_node','duplicate_node','node_order',
    'tags_missing','tags_decimal','node_tag','missing_routes','extra_routes','route_order',
    'statement','script','dependencies','statement_digest','bundle_node_id',
    'node_alpha','node_enrolled','node_stable','defined_flag','defined_digest',
    'defined_false_formula','defined_open_formula',
    'report_extra_full_goal_claim','report_schema','report_worker_count','report_principals_flag',
    'report_published','report_rss_bool','state_rows_changed',
)


def test_same_live_mutation_inventory_is_exact_and_never_a_positive_mock():
    assert len(ACTUAL_EVIDENCE_MUTATIONS)==len(set(ACTUAL_EVIDENCE_MUTATIONS))==44


def assert_same_live_campaign(files,corpus,report,state,selection):
    """Assert the reader's actual retained eight-worker output, not a receipt."""
    root,pin=campaign._research_evidence(corpus,report,state,selection)
    parents=campaign.parent_files()
    original,parent_graph,parent_audit=campaign._parent_context(parents)
    actual,graph,audit=(json.loads(files[name]) for name in ('campaign.json','definitions.json','dag-audit.json'))
    old={row['id']:row for row in original['nodes']}
    assert len(actual['nodes'])==144 and len({row['id'] for row in actual['nodes']})==144
    assert [r['id'] for r in actual['nodes']]==[r['id'] for r in original['nodes']]
    assert all(row==old[row['id']] for row in actual['nodes'] if row['id']!='G091')
    assert all(row['status']==old[row['id']]['status'] and row['statement']==old[row['id']]['statement']
               and row['deps']==old[row['id']]['deps'] and row.get('evidence')==old[row['id']].get('evidence')
               for row in actual['nodes'])
    assert {key:value for key,value in actual['meta'].items() if key not in META_ADDITIONS}==original['meta']
    assert all(actual['ambitious_boundaries'][name]==value for name,value in original['ambitious_boundaries'].items())
    assert actual['sources'][:len(original['sources'])]==original['sources']
    assert {row['id'] for row in actual['sources'][len(original['sources']):]}=={'S85','S86','S87','S88'}
    progress=_goal(actual)['polynomial_prerequisite_progress']
    assert _goal(actual)['status']=='open'
    assert progress['full_G091_proved'] is progress['alpha_enrolled'] is progress['checked_use'] is progress['stable_member'] is False
    assert (progress['new_theorem_count'],progress['inherited_alpha_theorem_count'],progress['complete_cone_theorem_count'])==(85,207,292)
    assert progress['principal_roots']==report['principal_roots']
    assert progress['representative_theorem_name']==EXPECTED_ROOTS[-1] and progress['representative_proof_tag']=='PQ0055'
    assert progress['representative_statement_sha256']==root['statement_sha256']
    assert progress['bundle_sha256']==pin.sha256 and progress['ordinary_principal_count']==6
    assert corpus['tags']=={row.name:f'PQ{index:04X}' for index,row in enumerate(state.rows,1)}
    assert tuple(corpus['root_names'])==EXPECTED_ROOTS
    assert len(actual['definitions'])==len(original['definitions'])+7
    assert all(actual['definitions'][name]==row for name,row in original['definitions'].items())
    for identifier,name in EXPECTED_DEFINITIONS:
        item=definitions.ALL_CONSTRUCTIVE_DEFINITIONS_BY_NAME[name]
        assert actual['definitions'][name]['reviewed_definition_id']==identifier
        assert actual['definitions'][name]['reviewed_expansion_sha256']==sha256(item.template_source.encode()).hexdigest()
    assert all(audit[key]==parent_audit[key] for key in UNTOUCHED_AUDIT)
    assert audit['inherited_proof_dag_boundary']['alpha_proof_dag_recomputed_here'] is False
    separate=audit['polynomial_prerequisite_proof_dag']
    assert (separate['theorem_count'],separate['new_theorem_count'],separate['inherited_alpha_theorem_count'])==(292,85,207)
    assert separate['ordered_names_sha256']==selection.plan.ordered_names_sha256
    assert separate['dependency_edges']==selection.plan.dependency_edge_count
    assert separate['bundle_sha256']==pin.sha256 and separate['ordinary_principal_count']==6
    assert separate['full_G091_proved'] is separate['alpha_admission_performed'] is separate['stable_admission_performed'] is False
    assert separate['all_theorem_bodies_original_ha_checked'] is separate['same_bytes_compiled_lean_checked'] is True
    assert (graph['reviewed_definition_count'],graph['reviewed_definition_edge_count'])==(390,844)
    _definition_dags(actual,graph)
    html=files['index.html'].decode()
    match=re.search(r'<script type="application/json" id="campaign-data">(.*?)</script>',html,flags=re.S)
    assert match and json.loads(match[1])==actual
    assert _function(html,'proved')==_function(parents['index.html'].decode(),'proved')
    assert not re.search(r'^\s*G091:',html,flags=re.M)
    assert campaign.parent_files()==parents


def assert_same_live_evidence_rejected(corpus,report,state,selection,attack):
    """Mutate only the reader's actual live inputs; no accepting checker mock."""
    assert attack in ACTUAL_EVIDENCE_MUTATIONS
    changed_corpus,changed_report=deepcopy(corpus),deepcopy(report)
    changed_state=state
    node=changed_corpus['nodes'][0]
    if attack=='wrong_bundle_report': changed_report['checkpoint']['bundle']['sha256']='0'*64
    elif attack=='missing_ordinary': changed_report['principal_roots'].pop()
    elif attack=='extra_ordinary': changed_report['principal_roots'].append(deepcopy(changed_report['principal_roots'][0]))
    elif attack=='ordinary_order': changed_report['principal_roots'].reverse()
    elif attack=='ordinary_statement': changed_report['principal_roots'][0]['statement_sha256']='0'*64
    elif attack=='ordinary_count_zero': changed_report['principal_roots'][0]['ordinary_certificate_nodes']=0
    elif attack=='ordinary_count_bool': changed_report['principal_roots'][0]['ordinary_certificate_nodes']=True
    elif attack=='ordinary_count_overflow': changed_report['principal_roots'][0]['ordinary_certificate_nodes']=campaign.support.closure.DEFAULT_LAYERED_REPLAY_LIMITS.max_candidate_proof_occurrences+1
    elif attack=='novelty_missing': changed_report.pop('novelty')
    elif attack=='novelty_duplicate': changed_report['novelty']['exact_statement_ast_duplicates']=[['new','old']]
    elif attack=='corpus_family': changed_corpus['family_slug']='foreign'
    elif attack=='corpus_count': changed_corpus['node_count']=84
    elif attack=='alpha_count': changed_corpus['alpha_checked_use_node_count']=1
    elif attack=='enrolled_count': changed_corpus['alpha_enrolled_node_count']=1
    elif attack=='stable_count': changed_corpus['stable_admitted_node_count']=1
    elif attack=='corpus_bundle': changed_corpus['proof_bundle_sha256']='0'*64
    elif attack=='missing_node': changed_corpus['nodes'].pop()
    elif attack=='duplicate_node': changed_corpus['nodes'][-1]=deepcopy(node)
    elif attack=='node_order': changed_corpus['nodes'].reverse()
    elif attack=='tags_missing': changed_corpus['tags'].pop(node['name'])
    elif attack=='tags_decimal': changed_corpus['tags']={row.name:f'PQ{index:04d}' for index,row in enumerate(state.rows,1)}
    elif attack=='node_tag': node['id']='PQFFFF'
    elif attack=='missing_routes': changed_corpus['root_names'].pop()
    elif attack=='extra_routes': changed_corpus['root_names'].append(state.rows[0].name)
    elif attack=='route_order': changed_corpus['root_names'].reverse()
    elif attack=='statement': node['statement']='0=1'
    elif attack=='script': node['script']=['NOT A PROOF']
    elif attack=='dependencies': node['dependencies']=['invented_dependency']
    elif attack=='statement_digest': node['statement_sha256']='0'*64
    elif attack=='bundle_node_id': node['proof_bundle_node_id']=-1
    elif attack=='node_alpha': node['alpha_checked_use']=True
    elif attack=='node_enrolled': node['admitted_to_alpha']=True
    elif attack=='node_stable': node['stable_member']=True
    elif attack=='defined_flag': node['defined']['exact_ast_equivalence']=False
    elif attack=='defined_digest': node['defined']['expanded_statement_sha256']='0'*64
    elif attack=='defined_false_formula': node['defined']['defined_statement']='0=1'
    elif attack=='defined_open_formula': node['defined']['defined_statement']='injected_context=injected_context'
    elif attack=='report_extra_full_goal_claim': changed_report['full_G091_proved']=True
    elif attack=='report_schema': changed_report['schema']='peano-g009-local-research-checkpoint-v1'
    elif attack=='report_worker_count': changed_report['fresh_worker_count']=7
    elif attack=='report_principals_flag': changed_report['polynomial_prerequisite_principals_checked']=False
    elif attack=='report_published': changed_report['published']=True
    elif attack=='report_rss_bool': changed_report['peak_rss_bytes']=True
    elif attack=='state_rows_changed': changed_state=replace(state,rows=(replace(state.rows[0],statement='0=1'),*state.rows[1:]))
    with pytest.raises(campaign.support.PolynomialDivisionError):
        campaign._research_evidence(changed_corpus,changed_report,changed_state,selection)
