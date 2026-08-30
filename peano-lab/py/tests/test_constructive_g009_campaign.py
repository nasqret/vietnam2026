"""Independent atlas projection tests, never substitute proof authority.

The private formatter fixtures below are explicitly NOT PROOF EVIDENCE.
They exercise only _project, _html and conservative definition formatting;
they never enter a fresh proof gate or the public verified-reader builder.
The final helper is for the reader's actual same-live eight-worker tests.
It cannot manufacture that evidence or read a stored success receipt.
"""

from copy import deepcopy
from dataclasses import fields, is_dataclass, replace
from hashlib import sha256
import importlib
import inspect
import json
from pathlib import Path
import re
import subprocess
import sys
from types import SimpleNamespace

import pytest

# Observe this module's own imports and operations, not other CI modules.
_WATCHED_MODULE_ROOTS = ('peano_lab.library.editions_v31',)


def _tracked_module_identities(modules=None):
    modules = sys.modules if modules is None else modules
    return {name:module for name,module in modules.items()
            if any(name == root or name.startswith(root+'.') for root in _WATCHED_MODULE_ROOTS)}


def _assert_tracked_modules_unchanged(before,modules=None):
    after = _tracked_module_identities(modules)
    assert after.keys() == before.keys(), 'authority module inventory changed'
    assert all(after[name] is module for name,module in before.items()), 'authority module identity changed'


@pytest.fixture(autouse=True)
def _authority_module_baseline():
    before = _tracked_module_identities()
    yield before
    _assert_tracked_modules_unchanged(before)


_PROJECT_IMPORT_MODULES_BEFORE = _tracked_module_identities()

import extend_constructive_g009_campaign as campaign
import constructive_g009_definitions as definitions
from constructive_formula_compactor import _LocalDefinedParser
from peano_lab.kernel.formulas import parse_formula_in_context, parse_formula_with_names
from peano_lab.library.theorems import TheoremSpec
from sync_constructive_grand_campaign import _definition_dags, _milestone_dag, CampaignDagError


NOTICE = 'FORMATTER FIXTURE ONLY: NOT PROOF EVIDENCE, NOT A VERIFIED RELEASE'
COMPONENT_PINS = {
    'dirichlet_convolution_table_exists_extensionally_unique':'dd3b6ce98b1cda129a5105bc176ffbb4e7ca7d9549ea61a8ddcfc53a4a1ced13',
    'dirichlet_convolution_associative':'7963b56c370b9ff42ae43dc3e12d13dd36b6bd1dd356b62269a062a6a90d6738',
    'dirichlet_delta_unit_exists':'6924256ebdc7a4a8b46c532d5808e5794dea1430b6d1892c764a826191b4d710',
    'dirichlet_inverse_positive_criterion':'b2130664b7580d7fbeaeb33ebed7c27718cd89676a2b893198751a39ce38d54d',
}
COMPONENT_MODULES = (
    'dirichlet_convolution_candidate','dirichlet_associativity_candidate',
    'dirichlet_units_candidate','dirichlet_inverse_candidate',
)
META_ADDITIONS = {'g009_research_new_theorem_count','g009_research_full_goal_proved',
                  'g009_research_alpha_admission','g009_research_release_date'}


def _same_ast(first,second):
    pending,seen = [(first,second)],set()
    while pending:
        left,right = pending.pop()
        assert type(left) is type(right)
        key = id(left),id(right)
        if key in seen:
            continue
        seen.add(key)
        if is_dataclass(left):
            pending.extend((getattr(left,field.name),getattr(right,field.name)) for field in fields(left))
        else:
            assert left == right


def _old_definition_record(item):
    return {'parameters':list(item.parameters),'meaning':item.summary,
            'expansion':item.template_source,'reviewed_definition_id':item.stable_id,
            'fixture_notice':NOTICE}


@pytest.fixture(scope='module')
def formatting():
    """Tiny structural parent/catalog, not the actual 3796 theorem objects."""
    tools = [f'T{i:02d}' for i in range(1,17)]
    anchors = [f'A{i:02d}' for i in range(1,9)]
    goals = [f'G{i:03d}' for i in range(1,121)]
    nodes = []
    for identifier in (*tools,*anchors,*goals):
        kind = 'tool' if identifier.startswith('T') else 'anchor' if identifier.startswith('A') else 'goal'
        nodes.append({'id':identifier,'kind':kind,'title':NOTICE+' '+identifier,
            'statement':'Multiplicative(f)' if identifier == 'G009' else '0=0',
            'status':'open','layer':0,'family':'FixtureFamily' if kind == 'goal' else None,
            'deps':[],'conceptual_refs':[],'definition_refs':[],
            'evidence':{'checked_use':False,'fixture_notice':NOTICE},
            'references':['S01'],'fixture_notice':NOTICE})
    old_definitions = {name:_old_definition_record(item)
                       for name,item in definitions.HISTORICAL_DEFINITIONS_BY_NAME.items()}
    old_definitions['Multiplicative'] = {'parameters':['f'],'meaning':NOTICE,
        'expansion':'Unreviewed arithmetic function planning vocabulary.'}
    original = {'schema':'constructive-grand-campaign-v1','fixture_notice':NOTICE,
        'meta':{'current_alpha_version':'v31','current_alpha_checked_use_count':3796,
                'current_stable_count':432,'stable_count':432,'goal_count':120,'tool_count':16,
                'anchor_count':8,'node_count':144,'max_layer':0,'fixture_notice':NOTICE},
        'nodes':nodes,'definitions':old_definitions,
        'families':[{'id':'FixtureFamily','slug':'formatter-only-family','goal_ids':goals}],
        'layers':[{'number':0}],
        'sources':[{'id':'S01','kind':'formatter_fixture','path':'NOT_A_PROOF','label':NOTICE}],
        'ambitious_boundaries':{'alpha_v31_edition':{'role':'current_immutable_release',
            'catalog_sha256':campaign.CATALOG_SHA256,'theorem_count':3796,'checked_use_count':3796,
            'stable_count':432,'fixture_notice':NOTICE},
            'untouched_history':{'fixture_notice':NOTICE,'immutable':True}}}
    # Deliberately not valid proof records. No checker accepts these placeholders.
    records = [{'name':name,'checked_use':True,'statement_sha256':pin,'fixture_notice':NOTICE}
               for name,pin in COMPONENT_PINS.items()]
    records.extend({'name':f'formatter_catalog_{i:04d}','checked_use':False,'fixture_notice':NOTICE}
                   for i in range(3796-len(records)))
    catalog = {'schema':'peano-library-alpha-snapshot-v31','checked_use_count':3796,
               'theorems':records,'fixture_notice':NOTICE}
    names = [*campaign.checkpoints.PRINCIPAL_ROOTS,
             *(f'formatter_research_{i:04d}' for i in range(84))]
    tags = {name:f'MX{i:04X}' for i,name in enumerate(names,1)}
    root = {'name':campaign.ROOT_NAME,'id':tags[campaign.ROOT_NAME],
            'statement_sha256':'a'*64,'proof_bundle_node_id':1,
            'defined':{'defined_statement':'forall N F. MultiplicativePrefix(N,F) -> MultiplicativePrefix(N,F)',
                       'statement_definition_uses':{'ND0316':2}},'fixture_notice':NOTICE}
    corpus = {'nodes':[{'name':name,'fixture_notice':NOTICE} for name in names],
              'root_names':list(campaign.checkpoints.PRINCIPAL_ROOTS),'tags':tags,
              'family_title':NOTICE,'fixture_notice':NOTICE}
    pin = campaign.checkpoints.ArtifactPin('FORMATTER_ONLY_NOT_PROOF.json',1,'b'*64,462,1,1)
    report = {'principal_roots':[{'name':name,'fixture_notice':NOTICE}
                                 for name in campaign.checkpoints.PRINCIPAL_ROOTS],
              'fixture_notice':NOTICE}
    before = deepcopy((original,catalog,corpus,root,report))
    projected = campaign._project(original,catalog,corpus,root,pin,report)
    assert (original,catalog,corpus,root,report) == before
    graph = campaign.build_definition_graph(projected)
    return SimpleNamespace(original=original,catalog=catalog,corpus=corpus,root=root,pin=pin,
                           report=report,projected=projected,graph=graph)


def _goal(value):
    return next(row for row in value['nodes'] if row['id'] == 'G009')


def test_exact_four_inherited_contracts_match_unchanged_actual_factories():
    assert campaign.INHERITED_COMPONENTS == tuple(COMPONENT_PINS)
    for module_name,name in zip(COMPONENT_MODULES,COMPONENT_PINS,strict=True):
        module = importlib.import_module('peano_lab.library.'+module_name)
        rows = getattr(module,'make_'+module_name+'_theorems')(TheoremSpec)
        row = next(row for row in rows if row.name == name)
        assert sha256(row.statement.encode()).hexdigest() == COMPONENT_PINS[name]
    assert 'dirichlet_inverse_criterion' not in campaign.INHERITED_COMPONENTS
    assert 'dirichlet_inverse_positive_criterion' in campaign.INHERITED_COMPONENTS


def test_formatter_preserves_every_143_other_node_and_all_parent_metadata(formatting):
    first,after = formatting.original,formatting.projected
    original_nodes = {row['id']:row for row in first['nodes']}
    assert len(after['nodes']) == len(original_nodes) == 144
    assert [row['id'] for row in after['nodes']] == [row['id'] for row in first['nodes']]
    unrelated = [row for row in after['nodes'] if row['id'] != 'G009']
    assert len(unrelated) == 143
    assert all(row == original_nodes[row['id']] for row in unrelated)
    assert {key:value for key,value in after['meta'].items() if key not in META_ADDITIONS} == first['meta']
    assert set(after['meta'])-set(first['meta']) == META_ADDITIONS
    assert after['meta']['current_alpha_checked_use_count'] == 3796
    assert after['meta']['current_stable_count'] == after['meta']['stable_count'] == 432
    for key in set(first)-{'nodes','meta','definitions','sources','ambitious_boundaries'}:
        assert after[key] == first[key]
    assert {key:value for key,value in after['ambitious_boundaries'].items()
            if key != 'g009_local_research_completion'} == first['ambitious_boundaries']


def test_research_closed_status_does_not_count_any_new_alpha_or_stable_rows(formatting):
    goal = _goal(formatting.projected)
    evidence = goal['evidence']
    assert goal['status'] == 'available' and goal['research_proof_closed'] is True
    assert evidence['checked_use'] is evidence['alpha_enrolled'] is evidence['stable_member'] is False
    assert evidence['research_new_theorem_count'] == 90
    assert evidence['full_G009_finite_coded_contract_proved'] is True
    assert evidence['multiplicative_convolution_closure_proved'] is True
    assert evidence['inverse_multiplicativity_claimed'] is False
    assert evidence['normalization_at_one_for_multiplicativity'] == '+1 only'
    assert evidence['inverse_criterion_includes_both_signed_units'] is True
    assert evidence['unrestricted_zero_values'] is evidence['positive_represented_value_uniqueness'] is True
    assert evidence['checked_theorem_names'] == list(COMPONENT_PINS)
    assert set(evidence['checked_theorem_names']).isdisjoint(row['name'] for row in formatting.corpus['nodes'])
    assert 'theorem_name' not in evidence and evidence['research_theorem_name'] == campaign.ROOT_NAME
    boundary = formatting.projected['ambitious_boundaries']['g009_local_research_completion']
    assert (boundary['new_theorem_count'],boundary['inherited_theorem_count'],boundary['complete_cone_theorem_count']) == (90,371,461)
    assert boundary['ordinary_principal_count'] == 6 and boundary['alpha_admission_performed'] is False
    assert boundary['G091_general_prime_power_fields'] == 'open'
    assert _goal(formatting.original)['status'] == 'open'


def test_exact_inherited_component_provenance_is_copied_not_recounted(formatting):
    goal = _goal(formatting.projected)
    assert goal['historical_alpha_v31_evidence'] == _goal(formatting.original)['evidence']
    assert goal['historical_planned_statement'] == _goal(formatting.original)['statement']
    assert goal['evidence']['inherited_contract_components'] == [
        {'name':name,'statement_sha256':digest,'alpha_version':'v31','checked_use':True}
        for name,digest in COMPONENT_PINS.items()]
    assert goal['evidence']['research_principal_roots'] == formatting.report['principal_roots']
    assert formatting.projected['sources'][:len(formatting.original['sources'])] == formatting.original['sources']
    new_sources = formatting.projected['sources'][len(formatting.original['sources']):]
    assert [row['id'] for row in new_sources] == ['S81','S82','S83','S84']
    assert len({row['id'] for row in formatting.projected['sources']}) == len(formatting.projected['sources'])
    assert new_sources[-1]['path'] == 'book/_static/constructive-completed-lower-campaign-v31/campaign.json'


def test_all_old_definition_records_and_planning_multiplicative_remain_literal(formatting):
    first,after = formatting.original['definitions'],formatting.projected['definitions']
    assert all(after[name] == value for name,value in first.items())
    assert set(after)-set(first) == {item.name for item in definitions.G009_DEFINITIONS}
    assert len(after)-len(first) == 11
    assert after['Multiplicative'] == first['Multiplicative']
    graph_rows = {row['name']:row for row in formatting.graph['definitions']}
    assert graph_rows['Multiplicative']['reviewed_match'] is None
    assert graph_rows['MultiplicativePrefix']['reviewed_match']['reviewed_id'] == 'ND0316'


@pytest.mark.parametrize('item',definitions.G009_DEFINITIONS,ids=lambda item:item.name)
def test_each_campaign_definition_is_an_exact_compact_first_order_graph(formatting,item):
    record = formatting.projected['definitions'][item.name]
    assert record['parameters'] == list(item.parameters)
    assert record['reviewed_definition_id'] == item.stable_id
    assert record['reviewed_expansion_sha256'] == sha256(item.template_source.encode()).hexdigest()
    assert record['meaning'] == item.summary and record['exact_defined_expansion_equivalence_checked'] is True
    aliases = {**definitions.ALL_CONSTRUCTIVE_DEFINITIONS_BY_NAME,
               'BetaSum':replace(definitions.ALL_CONSTRUCTIVE_DEFINITIONS_BY_NAME['Sum'],name='BetaSum')}
    parser = _LocalDefinedParser(record['expansion'],aliases)
    parser.free = list(item.parameters)
    _same_ast(parser.parse(),item.template_formula)
    assert tuple(parser.free) == item.parameters
    assert not re.search(r'\bSum\(',record['expansion'])


def test_notation_dag_and_milestone_dependencies_do_not_become_alpha_proof_edges(formatting):
    graph = formatting.graph
    assert (graph['reviewed_definition_count'],graph['reviewed_definition_edge_count']) == (383,825)
    assert {row['kind'] for row in graph['definition_edges']} == {'definition_uses_definition'}
    assert {row['kind'] for row in graph['milestone_usage_edges']} <= {'statement_uses_definition','declared_notation'}
    before,before_edges = _milestone_dag(formatting.original)
    after,after_edges = _milestone_dag(formatting.projected)
    assert before == after and before_edges == after_edges
    _definition_dags(formatting.projected,graph)
    assert all(row['blueprint_expansion_is_kernel_checked'] is False for row in graph['compatible_reviewed_matches'])
    assert all(row['authority'] == 'blueprint-vocabulary-only' for row in graph['definitions'])


@pytest.mark.parametrize('attack',('definition_as_proof','usage_as_proof','cross_namespace'))
def test_wrong_graph_edge_categories_fail_closed(formatting,attack):
    graph = deepcopy(formatting.graph)
    if attack == 'definition_as_proof': graph['definition_edges'][0]['kind'] = 'proof_dependency'
    elif attack == 'usage_as_proof': graph['milestone_usage_edges'][0]['kind'] = 'proof_dependency'
    else: graph['milestone_usage_edges'][0]['target'] = 'G009'
    with pytest.raises(CampaignDagError):
        _definition_dags(formatting.projected,graph)


@pytest.mark.parametrize('attack',('schema','version','alpha_count','goal_count','node_count',
                                  'catalog_schema','catalog_count','catalog_rows','G009_closed','G091_closed',
                                  'new_alpha_collision','definition_shadow','source_shadow'))
def test_pure_projection_rejects_wrong_or_shadowed_parent_inventory(formatting,attack):
    original,catalog,corpus,root,report = deepcopy((formatting.original,formatting.catalog,
                                                 formatting.corpus,formatting.root,formatting.report))
    if attack == 'schema': original['schema'] = 'foreign'
    elif attack == 'version': original['meta']['current_alpha_version'] = 'v30'
    elif attack == 'alpha_count': original['meta']['current_alpha_checked_use_count'] = 3797
    elif attack == 'goal_count': original['meta']['goal_count'] = 119
    elif attack == 'node_count': original['nodes'].pop()
    elif attack == 'catalog_schema': catalog['schema'] = 'foreign'
    elif attack == 'catalog_count': catalog['checked_use_count'] = 3795
    elif attack == 'catalog_rows': catalog['theorems'].pop()
    elif attack == 'G009_closed': _goal(original)['status'] = 'alpha_closed'
    elif attack == 'G091_closed': next(row for row in original['nodes'] if row['id'] == 'G091')['status'] = 'available'
    elif attack == 'new_alpha_collision': corpus['nodes'][0]['name'] = next(iter(COMPONENT_PINS))
    elif attack == 'definition_shadow': original['definitions']['MultiplicativePrefix'] = {'unreviewed':True}
    else: original['sources'].append({'id':'S81','kind':'unreviewed','label':NOTICE})
    with pytest.raises(campaign.support.G009Error):
        campaign._project(original,catalog,corpus,root,formatting.pin,report)


@pytest.mark.parametrize('name',tuple(COMPONENT_PINS))
@pytest.mark.parametrize('attack',('missing','not_checked'))
def test_each_inherited_contract_component_is_required(formatting,name,attack):
    catalog = deepcopy(formatting.catalog)
    row = next(row for row in catalog['theorems'] if row['name'] == name)
    if attack == 'missing': row['name'] = 'missing_component_placeholder'
    else: row['checked_use'] = False
    with pytest.raises(campaign.support.G009Error,match='component is missing'):
        campaign._project(formatting.original,catalog,formatting.corpus,formatting.root,formatting.pin,formatting.report)


@pytest.mark.parametrize('entrypoint',('parent_files','source_binding','build_files_for_verified_reader'))
def test_absent_parent_pins_stop_public_paths_before_catalog_or_evidence(monkeypatch,entrypoint):
    monkeypatch.setattr(campaign,'PARENT_PINS',{})
    def forbidden(*_args,**_kwargs):
        pytest.fail('unregistered parent reached an evidence or catalog access')
    monkeypatch.setattr(campaign,'load_catalog',forbidden)
    monkeypatch.setattr(campaign,'verify_catalog_bindings',forbidden)
    monkeypatch.setattr(campaign,'_research_evidence',forbidden)
    with pytest.raises(campaign.support.G009Error,match='pins are not registered'):
        function = getattr(campaign,entrypoint)
        function(*((None,)*4 if entrypoint == 'build_files_for_verified_reader' else ()))


def _fake_typed_syntax():
    """Forged counts must still fail: these formulas and scripts are false."""
    rows = tuple(TheoremSpec(f'not_a_proof_{i:04d}','0=1',(),('NOT A PROOF',),NOTICE) for i in range(90))
    state = campaign.support.CandidateState(rows,(),'0'*64)
    selected = campaign.support.SupportSelection(rows,(),tuple(f'fake_parent_{i}' for i in range(371)),(),None,
                                                 (*rows,*((rows[0],)*371)))
    report = {'fresh_worker_count':8,'schema':'peano-g009-local-research-checkpoint-v1',
              'multiplicative_convolution_principals_checked':True,
              'stored_receipt_is_proof_authority':False,'alpha_admission_performed':False,
              'stable_admission_performed':False,'published':False,'fixture_notice':NOTICE}
    return state,selected,report


@pytest.mark.parametrize('attack',('state_type','selection_type','owned_count','owned_changed','cross_support',
                                  'cone_count','inherited_count','worker_count','schema','no_principals',
                                  'saved_receipt','alpha','stable','published'))
def test_fake_or_incomplete_evidence_stops_before_artifact_access(monkeypatch,attack):
    state,selected,report = _fake_typed_syntax()
    if attack == 'state_type': state = object()
    elif attack == 'selection_type': selected = object()
    elif attack == 'owned_count': state = replace(state,rows=state.rows[:-1])
    elif attack == 'owned_changed': selected = replace(selected,owned=tuple(reversed(selected.owned)))
    elif attack == 'cross_support': selected = replace(selected,current_support=('not_owned',))
    elif attack == 'cone_count': selected = replace(selected,complete_specs=selected.complete_specs[:-1])
    elif attack == 'inherited_count': selected = replace(selected,parent_support=selected.parent_support[:-1])
    elif attack == 'worker_count': report['fresh_worker_count'] = 7
    elif attack == 'schema': report['schema'] = 'saved_success'
    elif attack == 'no_principals': report['multiplicative_convolution_principals_checked'] = False
    elif attack == 'saved_receipt': report['stored_receipt_is_proof_authority'] = True
    elif attack == 'alpha': report['alpha_admission_performed'] = True
    elif attack == 'stable': report['stable_admission_performed'] = True
    else: report['published'] = True
    monkeypatch.setattr(campaign.checkpoints,'require_final_inventory',
                        lambda:pytest.fail('invalid evidence reached artifact access'))
    with pytest.raises(campaign.support.G009Error,match='incomplete or mislabelled'):
        campaign._research_evidence({},report,state,selected)


def test_all_true_flags_and_typed_counts_are_not_a_substitute_for_final_pins(monkeypatch):
    state,selected,report = _fake_typed_syntax()
    monkeypatch.setattr(campaign.support,'MATH_SOURCE_PINS',())  # A rejecting gate, never accepting fake evidence.
    with pytest.raises(campaign.support.G009Error,match='not sealed'):
        campaign._research_evidence({},report,state,selected)


HTML_FIXTURE = '''<!doctype html><title>FORMATTER FIXTURE ONLY, NOT PROOF EVIDENCE</title>
<header class="campaign-header"><nav aria-label="Proof library navigation">
<a href="../constructive-frontier-explorer/index.html" data-proof-home>Constructive proof families</a>
<a href="../pa-proof-explorer/defined/index.html" data-proof-quadratic>Quadratic Reciprocity</a>
<a href="../bertrand-proof-explorer/defined/index.html" data-proof-bertrand>Bertrand's Postulate</a>
</nav></header>
<script type="application/json" id="campaign-data">{"fixture_notice":"NOT PROOF EVIDENCE"}</script>
<script>
      var COMPILED_DEFINITIONS = {
      };
      var INCOMPATIBLE_DEFINITIONS = {
      };
      var PROOF_ROOTS = {
        T01: {route:"arithmetic-foundations",tag:"AF0001"}
      };
      function explorerBase(route) {
        var deployed = /\\/proofs\\/grand-campaign(?:\\/|$)/.test(window.location.pathname || "");
        if (deployed) return "../" + route + "/explorer/defined/";
        var currentFamilies = {"mobius-inversion":"constructive-completed-lower-explorer-v31"};
        var directory = currentFamilies[route] || "constructive-historical-explorers-v31";
        return "../" + directory + "/" + route + "/explorer/defined/";
      }
      function proved(node) {
        return !!node && node.status === "alpha_closed" && !!node.evidence && node.evidence.checked_use === true;
      }
      function describeStatus(node) {
        return proved(node) ? "Old checked status" : "Open";
      }
      function statusCaveat(node) {
        return "Old caveat";
      }
      function proofHref(path) {
        return path + (path.indexOf("?") === -1 ? "?" : "&") + "v=6c9ebfb3c37e";
      }
      function configureHeader() {
        document.querySelector("[data-proof-home]").setAttribute("href",
          /\\/proofs\\/grand-campaign(?:\\/|$)/.test(window.location.pathname || "") ? "../index.html" :
            "../constructive-frontier-explorer/index.html");
        document.querySelector("[data-proof-quadratic]").setAttribute("href",
          explorerBase("quadratic-reciprocity") + "index.html");
        document.querySelector("[data-proof-bertrand]").setAttribute("href",
          explorerBase("bertrand-postulate") + "index.html");
      }
</script>
'''


@pytest.fixture(scope='module')
def html_projection(formatting):
    return campaign._html(HTML_FIXTURE,formatting.projected,formatting.graph).decode()


def _javascript(source):
    matches = re.findall(r'<script>(.*?)</script>',source,flags=re.S)
    assert len(matches) == 1
    return matches[0]


def _run_js(source,expression,**values):
    harness = '''const fs=require("fs"),vm=require("vm");
const data=JSON.parse(fs.readFileSync(0,"utf8"));
const context=Object.assign({window:{location:{pathname:data.pathname||""}}},data.values);
vm.createContext(context);vm.runInContext(data.source,context,{timeout:1000});
const result=vm.runInContext(data.expression,context,{timeout:1000});
process.stdout.write(JSON.stringify(result));'''
    pathname = values.pop('pathname','')
    result = subprocess.run(['node','-e',harness],input=json.dumps({'source':_javascript(source),
        'expression':expression,'pathname':pathname,'values':values}),text=True,capture_output=True,timeout=15)
    assert result.returncode == 0,result.stderr
    assert not result.stderr
    return json.loads(result.stdout)


@pytest.mark.parametrize('pathname',('/proofs/grand-campaign/','/~fixture/proofs/grand-campaign/index.html'))
@pytest.mark.parametrize('route',('multiplicative-convolution','mobius-inversion','quadratic-reciprocity'))
def test_actual_generated_dispatcher_preserves_deployed_proof_routes(html_projection,pathname,route):
    assert _run_js(html_projection,'explorerBase(route)',pathname=pathname,route=route) == '../'+route+'/explorer/defined/'


@pytest.mark.parametrize('route,expected',(
    ('multiplicative-convolution','../multiplicative-convolution/explorer/defined/'),
    ('mobius-inversion','../../constructive-completed-lower-explorer-v31/mobius-inversion/explorer/defined/'),
    ('quadratic-reciprocity','../../constructive-historical-explorers-v31/quadratic-reciprocity/explorer/defined/'),
))
def test_actual_generated_dispatcher_fixes_raw_nested_atlas_routes(html_projection,route,expected):
    assert _run_js(html_projection,'explorerBase(route)',
                   pathname='/book/_static/constructive-g009-explorer/campaign/index.html',route=route) == expected


def test_initial_header_links_are_valid_before_javascript_in_either_layout(html_projection):
    header = re.search(r'<header class="campaign-header">(.*?)</header>',html_projection,flags=re.S)[1]
    revision = campaign.CATALOG_SHA256[:12]
    public = 'https://bnaskrecki.faculty.wmi.amu.edu.pl/proofs/'
    links = re.findall(r'<a href="([^"]+)" (data-proof-[a-z]+)>',header)
    assert dict((marker,href) for href,marker in links) == {
        'data-proof-home':'../index.html?v='+revision,
        'data-proof-quadratic':public+'quadratic-reciprocity/explorer/defined/index.html?v='+revision,
        'data-proof-bertrand':public+'bertrand-postulate/explorer/defined/index.html?v='+revision,
    }


@pytest.mark.parametrize('pathname,deployed',(
    ('/proofs/grand-campaign/',True),
    ('/~fixture/proofs/grand-campaign/index.html',True),
    ('/book/_static/constructive-g009-explorer/grand-campaign/index.html',False),
))
def test_configured_header_resolves_raw_and_public_routes_with_current_revision(html_projection,pathname,deployed):
    expression = '''(() => {
      const links={};
      globalThis.document={querySelector:(selector)=>({setAttribute:(name,value)=>{
        if(name!=="href") throw Error("not a navigation update"); links[selector]=value;
      }})};
      configureHeader(); return links;
    })()'''
    base = '../' if deployed else '../../constructive-historical-explorers-v31/'
    revision = campaign.CATALOG_SHA256[:12]
    assert _run_js(html_projection,expression,pathname=pathname) == {
        '[data-proof-home]':'../index.html?v='+revision,
        '[data-proof-quadratic]':base+'quadratic-reciprocity/explorer/defined/index.html?v='+revision,
        '[data-proof-bertrand]':base+'bertrand-postulate/explorer/defined/index.html?v='+revision,
    }


@pytest.mark.parametrize('marker',(
    'href="../constructive-frontier-explorer/index.html" data-proof-home',
    'href="../pa-proof-explorer/defined/index.html" data-proof-quadratic',
    'href="../bertrand-proof-explorer/defined/index.html" data-proof-bertrand',
    'document.querySelector("[data-proof-home]").setAttribute("href",',
    'explorerBase("quadratic-reciprocity") + "index.html");',
    'explorerBase("bertrand-postulate") + "index.html");',
))
@pytest.mark.parametrize('attack',('missing','duplicate'))
def test_header_navigation_rejects_changed_or_duplicate_parent_anchors(marker,attack):
    source = HTML_FIXTURE.replace(marker,'changed_marker',1) if attack == 'missing' else HTML_FIXTURE+HTML_FIXTURE
    with pytest.raises(campaign.support.G009Error,match='header navigation'):
        campaign._nested_navigation(source)


def test_html_embeds_exact_projection_and_distinguishes_research_status(formatting,html_projection):
    match = re.search(r'<script type="application/json" id="campaign-data">(.*?)</script>',html_projection,flags=re.S)
    assert match and json.loads(match[1]) == formatting.projected
    assert _run_js(html_projection,'localResearchProved(node)',node=_goal(formatting.projected)) is True
    assert _run_js(html_projection,'describeStatus(node)',node=_goal(formatting.projected)) == 'Independently proved research goal; not Alpha-admitted'
    caveat = _run_js(html_projection,'statusCaveat(node)',node=_goal(formatting.projected))
    assert '90 new research theorems are not Alpha or Stable admissions' in caveat
    assert _run_js(html_projection,'PROOF_ROOTS.G009.tag') == formatting.root['id']


@pytest.mark.parametrize('field,value',(('local_checkpoint_verified',False),('full_empty_context_closure',False),
    ('independent_lean_bundle_verified',False),('full_G009_finite_coded_contract_proved',False),
    ('checked_use',True),('alpha_enrolled',True),('stable_member',True),('checked_use',None)))
def test_display_status_rejects_incomplete_or_admitting_research_labels(formatting,html_projection,field,value):
    node = deepcopy(_goal(formatting.projected));node['evidence'][field] = value
    assert _run_js(html_projection,'localResearchProved(node)',node=node) is False


@pytest.mark.parametrize('field,value',(('id','G091'),('status','open'),('status','alpha_closed'),('research_proof_closed',False)))
def test_display_status_is_only_for_the_exact_research_goal(formatting,html_projection,field,value):
    node = deepcopy(_goal(formatting.projected));node[field] = value
    assert _run_js(html_projection,'localResearchProved(node)',node=node) is False


@pytest.mark.parametrize('attack',('compiled_table','incompatible_table','roots','duplicate_root','dispatcher',
                                  'duplicate_dispatcher','raw_return','proved','status','caveat','embedded_json'))
def test_html_rejects_changed_or_ambiguous_canonical_anchors(formatting,attack):
    source = HTML_FIXTURE
    replacements = {'compiled_table':'var COMPILED_DEFINITIONS = {','incompatible_table':'var INCOMPATIBLE_DEFINITIONS = {',
        'roots':'var PROOF_ROOTS = {','dispatcher':'var currentFamilies = ',
        'raw_return':'return "../" + directory + "/" + route + "/explorer/defined/";',
        'proved':'function proved(node) {','status':'function describeStatus(node) {',
        'caveat':'function statusCaveat(node) {','embedded_json':'id="campaign-data"'}
    if attack == 'duplicate_root': source = source.replace('      var PROOF_ROOTS = {\n','      var PROOF_ROOTS = {\n        G009: {},\n')
    elif attack == 'duplicate_dispatcher': source += '\n        var currentFamilies = {};\n'
    else: source = source.replace(replacements[attack],'changed_anchor',1)
    with pytest.raises((campaign.support.G009Error,ValueError)):
        campaign._html(source,formatting.projected,formatting.graph)


def test_unsafe_embedded_script_terminator_and_original_document_bound(formatting):
    value = deepcopy(formatting.projected);value['unsafe'] = '</ScRiPt><script>alert(1)</script>'
    with pytest.raises(campaign.support.G009Error,match='unsafe or oversized'):
        campaign._html(HTML_FIXTURE,value,formatting.graph)
    with pytest.raises(campaign.support.G009Error,match='8MiB'):
        campaign._json({'fixture_notice':NOTICE,'payload':'x'*(8*1024*1024)})
    assert campaign.MAX_CAMPAIGN_BYTES == 8*1024*1024


def test_public_builder_has_no_receipt_input_and_keeps_separate_checked_graphs():
    assert tuple(inspect.signature(campaign.build_files_for_verified_reader).parameters) == ('corpus','report','state','selection')
    source = inspect.getsource(campaign.build_files_for_verified_reader)
    assert source.index('source_binding()') < source.index('_research_evidence(') < source.index('_project(')
    assert source.index('validate_campaign_dags(') < source.index("data['research_proof_dag']")
    assert 'catalog=catalog' in source and "'notation_edges_are_proof_premises':False" in source
    assert 'parent_files() != parents or source_binding() != binding' in source
    assert 'write' not in source and 'read-report' not in source
    assert not hasattr(campaign,'main')


def assert_same_live_campaign(files,corpus,report,state,selection):
    """Call only from the actual reader run after all eight fresh proof jobs.

    This is a test assertion helper, not a fixture, factory, public builder,
    proof acceptance substitute or stored-report reader. The ordinary final
    source/artifact gate remains live; no positive checker is mocked here.
    """
    root,pin = campaign._research_evidence(corpus,report,state,selection)
    parents = campaign.parent_files()
    original = json.loads(parents['campaign.json'])
    old_audit = json.loads(parents['dag-audit.json'])
    actual = json.loads(files['campaign.json'])
    graph = json.loads(files['definitions.json'])
    audit = json.loads(files['dag-audit.json'])
    prior_nodes = {row['id']:row for row in original['nodes']}
    assert len(prior_nodes) == len(actual['nodes']) == 144
    assert [row['id'] for row in actual['nodes']] == [row['id'] for row in original['nodes']]
    assert sum(row['id'] != 'G009' for row in actual['nodes']) == 143
    assert all(row == prior_nodes[row['id']] for row in actual['nodes'] if row['id'] != 'G009')
    assert {key:value for key,value in actual['meta'].items() if key not in META_ADDITIONS} == original['meta']
    assert actual['ambitious_boundaries']['alpha_v31_edition'] == original['ambitious_boundaries']['alpha_v31_edition']
    assert all(actual['definitions'][name] == value for name,value in original['definitions'].items())
    assert len(actual['definitions'])-len(original['definitions']) == 11
    assert actual['sources'][:len(original['sources'])] == original['sources']
    goal = _goal(actual)
    assert goal['historical_alpha_v31_evidence'] == prior_nodes['G009']['evidence']
    assert goal['historical_planned_statement'] == prior_nodes['G009']['statement']
    assert goal['evidence']['checked_theorem_names'] == list(COMPONENT_PINS)
    assert goal['evidence']['inherited_contract_components'] == [
        {'name':name,'statement_sha256':digest,'alpha_version':'v31','checked_use':True}
        for name,digest in COMPONENT_PINS.items()]
    assert goal['evidence']['research_principal_roots'] == report['principal_roots']
    assert goal['evidence']['research_theorem_name'] == campaign.ROOT_NAME
    assert goal['evidence']['research_theorem_statement_sha256'] == root['statement_sha256']
    assert goal['evidence']['checked_use'] is goal['evidence']['alpha_enrolled'] is goal['evidence']['stable_member'] is False
    assert tuple(corpus['root_names']) == campaign.checkpoints.PRINCIPAL_ROOTS
    assert corpus['tags'] == {row['name']:row['id'] for row in corpus['nodes']}
    assert all(re.fullmatch(r'MX[0-9A-F]{4}',row['id']) for row in corpus['nodes'])
    assert corpus['tags'] == {row.name:f'MX{index:04X}' for index,row in enumerate(state.rows,1)}
    assert root['id'] == 'MX0059'
    assert len({row['id'] for row in corpus['nodes']}) == 90
    for key in ('alpha_version','catalog_sha256','theorem_count','theorem_edge_count','theorem_dag_sha256',
                'milestone_count','milestone_proof_edge_count','milestone_dag_sha256'):
        assert audit[key] == old_audit[key]
    assert audit['theorem_count'] == 3796
    separate = audit['research_proof_dag']
    assert (separate['theorem_count'],separate['new_theorem_count'],separate['inherited_alpha_theorem_count']) == (461,90,371)
    assert separate['ordered_names_sha256'] == selection.plan.ordered_names_sha256
    assert separate['dependency_edges'] == selection.plan.dependency_edge_count
    assert separate['bundle_sha256'] == pin.sha256 and separate['ordinary_principal_count'] == 6
    assert separate['all_theorem_bodies_original_ha_checked'] is separate['same_bytes_compiled_lean_checked'] is True
    assert separate['notation_edges_are_proof_premises'] is False
    assert (graph['reviewed_definition_count'],graph['reviewed_definition_edge_count']) == (383,825)
    _definition_dags(actual,graph)
    html = files['index.html'].decode()
    match = re.search(r'<script type="application/json" id="campaign-data">(.*?)</script>',html,flags=re.S)
    assert match and json.loads(match[1]) == actual
    exact,names = parse_formula_with_names(root['statement'])
    assert names == ()
    parser = _LocalDefinedParser(goal['statement'],definitions.ALL_CONSTRUCTIVE_DEFINITIONS_BY_NAME)
    _same_ast(parser.parse(),exact)
    assert parser.free == []
    assert campaign.parent_files() == parents


ACTUAL_EVIDENCE_MUTATIONS = (
    'wrong_bundle_report','missing_ordinary','extra_ordinary','ordinary_order',
    'ordinary_statement','ordinary_count_zero','ordinary_count_bool','ordinary_count_overflow',
    'novelty_missing','novelty_duplicate','corpus_family','corpus_count','alpha_count',
    'enrolled_count','stable_count','corpus_bundle','missing_node','duplicate_node','node_order',
    'tags_missing','tags_decimal','node_tag','missing_routes','extra_routes','route_order',
    'statement','script','dependencies','statement_digest','bundle_node_id',
    'node_alpha','node_enrolled','node_stable','defined_flag','defined_digest',
    'defined_false_formula','defined_open_formula',
)


def assert_same_live_evidence_rejected(corpus,report,state,selection,attack):
    """Negative mutation of genuinely supplied live evidence, never a mock.

    The reader may parameterize its actual snapshot tests over the literal
    mutations above. This performs only the original exact metadata/AST
    guard, not another proof replay or logical-catalogue load. Final source
    and artifact pins are still authenticated on every guard invocation.
    """
    assert attack in ACTUAL_EVIDENCE_MUTATIONS
    changed_corpus,changed_report = deepcopy(corpus),deepcopy(report)
    node = changed_corpus['nodes'][0]
    if attack == 'wrong_bundle_report': changed_report['checkpoint']['bundle']['sha256'] = '0'*64
    elif attack == 'missing_ordinary': changed_report['principal_roots'].pop()
    elif attack == 'extra_ordinary': changed_report['principal_roots'].append(deepcopy(changed_report['principal_roots'][0]))
    elif attack == 'ordinary_order': changed_report['principal_roots'].reverse()
    elif attack == 'ordinary_statement': changed_report['principal_roots'][0]['statement_sha256'] = '0'*64
    elif attack == 'ordinary_count_zero': changed_report['principal_roots'][0]['ordinary_certificate_nodes'] = 0
    elif attack == 'ordinary_count_bool': changed_report['principal_roots'][0]['ordinary_certificate_nodes'] = True
    elif attack == 'ordinary_count_overflow':
        changed_report['principal_roots'][0]['ordinary_certificate_nodes'] = (
            campaign.support.closure.DEFAULT_LAYERED_REPLAY_LIMITS.max_candidate_proof_occurrences+1)
    elif attack == 'novelty_missing': changed_report.pop('novelty')
    elif attack == 'novelty_duplicate': changed_report['novelty']['exact_statement_ast_duplicates'] = [['new','old']]
    elif attack == 'corpus_family': changed_corpus['family_slug'] = 'foreign'
    elif attack == 'corpus_count': changed_corpus['node_count'] = 89
    elif attack == 'alpha_count': changed_corpus['alpha_checked_use_node_count'] = 1
    elif attack == 'enrolled_count': changed_corpus['alpha_enrolled_node_count'] = 1
    elif attack == 'stable_count': changed_corpus['stable_admitted_node_count'] = 1
    elif attack == 'corpus_bundle': changed_corpus['proof_bundle_sha256'] = '0'*64
    elif attack == 'missing_node': changed_corpus['nodes'].pop()
    elif attack == 'duplicate_node': changed_corpus['nodes'][-1] = deepcopy(node)
    elif attack == 'node_order': changed_corpus['nodes'].reverse()
    elif attack == 'tags_missing': changed_corpus['tags'].pop(node['name'])
    elif attack == 'tags_decimal':
        changed_corpus['tags'] = {row.name:f'MX{index:04d}' for index,row in enumerate(state.rows,1)}
    elif attack == 'node_tag': node['id'] = 'MXFFFF'
    elif attack == 'missing_routes': changed_corpus['root_names'].pop()
    elif attack == 'extra_routes': changed_corpus['root_names'].append(state.rows[0].name)
    elif attack == 'route_order': changed_corpus['root_names'].reverse()
    elif attack == 'statement': node['statement'] = '0=1'
    elif attack == 'script': node['script'] = ['NOT A PROOF']
    elif attack == 'dependencies': node['dependencies'] = ['invented_dependency']
    elif attack == 'statement_digest': node['statement_sha256'] = '0'*64
    elif attack == 'bundle_node_id': node['proof_bundle_node_id'] = -1
    elif attack == 'node_alpha': node['alpha_checked_use'] = True
    elif attack == 'node_enrolled': node['admitted_to_alpha'] = True
    elif attack == 'node_stable': node['stable_member'] = True
    elif attack == 'defined_flag': node['defined']['exact_ast_equivalence'] = False
    elif attack == 'defined_digest': node['defined']['expanded_statement_sha256'] = '0'*64
    elif attack == 'defined_false_formula': node['defined']['defined_statement'] = '0=1'
    elif attack == 'defined_open_formula': node['defined']['defined_statement'] = 'injected_context=injected_context'
    with pytest.raises(campaign.support.G009Error):
        campaign._research_evidence(changed_corpus,changed_report,state,selection)


def test_pure_suite_imports_no_current_alpha_edition_or_successful_proof_data(_authority_module_baseline):
    _assert_tracked_modules_unchanged(_authority_module_baseline)
    assert NOTICE.startswith('FORMATTER FIXTURE ONLY')


@pytest.mark.parametrize('module_name',_WATCHED_MODULE_ROOTS)
@pytest.mark.parametrize('initial,mutation',(
    ('absent','unchanged'),('preloaded','unchanged'),('absent','insert'),
    ('absent','insert_none'),('preloaded','remove'),('preloaded','replace'),
    ('preloaded','extra_entry'),
))
def test_authority_module_identity_observation_is_exact(module_name,initial,mutation):
    # Private cache-shaped data only: never insert a fabricated edition into
    # sys.modules, call a proof gate, or supply an accepting authority fixture.
    modules = {'unrelated.cached.module':object()}
    if initial == 'preloaded': modules[module_name] = object()
    before = _tracked_module_identities(modules)
    if mutation == 'insert': modules[module_name] = object()
    elif mutation == 'insert_none': modules[module_name] = None
    elif mutation == 'remove': del modules[module_name]
    elif mutation == 'replace': modules[module_name] = object()
    elif mutation == 'extra_entry': modules[module_name+'.unexpected'] = object()
    if mutation == 'unchanged':
        _assert_tracked_modules_unchanged(before,modules)
    else:
        with pytest.raises(AssertionError,match='authority module'):
            _assert_tracked_modules_unchanged(before,modules)


# Collection itself must not add/remove/replace any watched authority module.
_assert_tracked_modules_unchanged(_PROJECT_IMPORT_MODULES_BEFORE)
