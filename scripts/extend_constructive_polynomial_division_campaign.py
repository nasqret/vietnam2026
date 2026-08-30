"""Same-live display of polynomial prerequisites, without closing G091.

There is no standalone publication command, stored-receipt input, Alpha
enrollment or proof-checking shortcut here.  The caller first completes the
eight fresh proof workers and supplies their retained syntax and live report.
The old Alpha and G009 DAG records are inherited from exact immutable atlas
bytes; new milestone/definition DAGs are checked separately.  They are never
misrepresented as a newly replayed Alpha catalogue.
"""

from __future__ import annotations

from copy import deepcopy
from dataclasses import replace
from hashlib import sha256
import json
from pathlib import Path
import re

import constructive_polynomial_division_support as support
import constructive_polynomial_division_checkpoints as checkpoints
from constructive_polynomial_division_definitions import (
    ALL_CONSTRUCTIVE_DEFINITIONS_BY_NAME as DEFINITIONS,
    POLYNOMIAL_DIVISION_DEFINITIONS, definition_closure,
)
from constructive_polynomial_division_definition_graph import build_definition_graph
from constructive_formula_compactor import _FormulaCompactor, _LocalDefinedParser
from extend_constructive_second_wave_campaign import _table_source
from peano_catalog_shards import verify_catalog_bindings
from sync_constructive_grand_campaign import (
    MAX_CAMPAIGN_BYTES, _definition_dags, _digest, _expected,
    _milestone_dag, _projection_digest,
)
from peano_lab.kernel.formulas import parse_formula_with_names
from peano_lab.library.theorems import TheoremSpec, _closed_formula


ROOT = support.ROOT
PARENT = ROOT/'book/_static/constructive-g009-explorer/grand-campaign'
PARENT_PINS = {
    'campaign.json': {'bytes':623714,'sha256':'5dd8a6c97f33643fbd030ab9420f9507069cd0e57c573152c2f65766522cb788'},
    'definitions.json': {'bytes':1455910,'sha256':'231c5974c698c62185f29c26e2ce35c447b61f14bd611932400b574c32748085'},
    'dag-audit.json': {'bytes':1581,'sha256':'5ea16177f405e482c69a846f3f04b9a8fc71e60d5933d4e57b0e6e4e39d62fbb'},
    'index.html': {'bytes':683902,'sha256':'604adbf407fb250fefbe33ed8badd8a6026fdba5207978d4509a54368982ea48'},
}
SLUG = 'polynomial-division-prerequisites'
READER_PACKAGE = 'constructive-polynomial-division-explorer'
TAG_PREFIX = 'PQ'
ROOT_NAME = 'prime_field_polynomial_synthetic_zero_remainder_iff'
CATALOG_PATH = 'artifacts/peano-library/alpha/catalog-v31.json'
CATALOG_SHA256 = '6c9ebfb3c37e42aefab200b710f78e7693dc5826c80f053544deea41caf44aab'
RFC_PATH = 'research/arithmetic-library/prime-field-polynomial-division-prerequisites-rfc-v1.md'
REPORT_SCHEMA = 'peano-polynomial-division-local-research-checkpoint-v1'
NEW_COUNT, INHERITED_COUNT, COMPLETE_COUNT = 85, 207, 292
REVIEWED_COUNT, REVIEWED_EDGES = 390, 844
REFINEMENT = (
    'Eighty-five independently proved local research theorems now construct '
    'canonical coefficient negation and subtraction, actual leading-zero '
    'trimming, normalization by a genuine leading-coefficient inverse, and '
    'synthetic division by X-a using an actual Horner history and quotient '
    'slice. The six principal endpoints have ordinary empty-context HA '
    'certificates and the complete dependency bundle is independently checked '
    'in Lean. These are polynomial prerequisites, not arbitrary-divisor '
    'Euclidean division, polynomial gcd, irreducible-polynomial existence, '
    'quotient-field construction, or general prime-power fields. G091 remains '
    'open. None of these 85 research statements is an Alpha or Stable admission.'
)
REMAINING = (
    'Arbitrary-divisor polynomial Euclidean division and its degree bound.',
    'Constructive polynomial gcd and Bezout arithmetic.',
    'Irreducible polynomials of every required positive degree.',
    'Actual quotient-field arithmetic tables and the p^k cardinality proof.',
)
META_ADDITIONS = {
    'polynomial_prerequisite_new_theorem_count':NEW_COUNT,
    'polynomial_prerequisite_complete_cone_count':COMPLETE_COUNT,
    'polynomial_prerequisite_alpha_admission':False,
    'polynomial_prerequisite_G091_closed':False,
    'polynomial_prerequisite_release_date':'2026-08-30',
}
REPORT_KEYS = frozenset((
    'schema','fresh_worker_count','stored_receipt_is_proof_authority','published',
    'alpha_admission_performed','stable_admission_performed','novelty','checkpoint',
    'principal_roots','polynomial_prerequisite_principals_checked','peak_rss_bytes',
))


def _error(message):
    raise support.PolynomialDivisionError(message)


def _json(value):
    data=(json.dumps(value,ensure_ascii=False,allow_nan=False,sort_keys=True,indent=2)+'\n').encode()
    if len(data)>MAX_CAMPAIGN_BYTES:
        _error('polynomial prerequisite campaign exceeds the unchanged 8 MiB bound')
    return data


def _document(raw):
    def pairs(items):
        result={}
        for key,value in items:
            if key in result:
                _error('a pinned atlas document repeats a JSON field')
            result[key]=value
        return result
    def constant(_value):
        _error('a pinned atlas document contains a non-finite JSON number')
    try:
        value=json.loads(raw.decode('utf-8'),object_pairs_hook=pairs,parse_constant=constant)
    except (TypeError,UnicodeError,ValueError,RecursionError) as error:
        raise support.PolynomialDivisionError('invalid bounded atlas JSON') from error
    if type(value) is not dict:
        _error('an atlas document must be an exact JSON object')
    return value


def parent_files():
    """Read the actual four immutable G009 atlas files, with literal pins."""
    if set(PARENT_PINS)!={'campaign.json','definitions.json','dag-audit.json','index.html'}:
        _error('the exact four-file G009 atlas parent is not registered')
    result={}
    for name,pin in PARENT_PINS.items():
        if (type(pin) is not dict or set(pin)!={'bytes','sha256'}
                or type(pin['bytes']) is not int or not 0<pin['bytes']<=MAX_CAMPAIGN_BYTES
                or type(pin['sha256']) is not str or re.fullmatch(r'[0-9a-f]{64}',pin['sha256']) is None):
            _error('invalid literal G009 atlas parent pin')
        support.check_pin(support.FilePin(name,pin['bytes'],pin['sha256']),PARENT,MAX_CAMPAIGN_BYTES)
        raw=support.bounded_bytes(PARENT/name,MAX_CAMPAIGN_BYTES)
        if len(raw)!=pin['bytes'] or sha256(raw).hexdigest()!=pin['sha256']:
            _error('the immutable G009 atlas changed while reading')
        result[name]=raw
    return result


def source_binding():
    """Bounded delivery/formatting identity; no Alpha or proof-state loading."""
    parents=parent_files()
    catalog=verify_catalog_bindings(ROOT/CATALOG_PATH,expected_sha256=CATALOG_SHA256)
    sources={
        Path(__file__).resolve(),
        ROOT/'scripts/constructive_polynomial_division_support.py',
        ROOT/'scripts/constructive_polynomial_division_checkpoints.py',
        ROOT/'scripts/check_constructive_polynomial_division.py',
        ROOT/'scripts/constructive_formula_compactor.py',
        ROOT/'scripts/extend_constructive_second_wave_campaign.py',
        ROOT/'scripts/sync_constructive_grand_campaign.py',
        ROOT/'scripts/peano_catalog_shards.py',
        ROOT/'peano-lab/py/peano_lab/library/bertrand_defined_edition.py',
        ROOT/'peano-lab/py/peano_lab/library/defined_edition.py',
        ROOT/'peano-lab/py/peano_lab/library/defined_syntax.py',
    }
    # Include the actual imported definition infrastructure, not only the
    # seven-row wrapper. Every file remains subject to the same bounded read.
    sources.update((ROOT/'scripts').glob('constructive_*definition*.py'))
    sources.update(ROOT/pin.path for pin in support.MATH_SOURCE_PINS)
    pins=[]
    for path in sorted(sources):
        raw=support.bounded_bytes(path,support.MAX_SOURCE_BYTES)
        pins.append((support._repository_path(path),len(raw),sha256(raw).hexdigest()))
    return sha256(support.canonical({
        'parents':{name:{'bytes':len(raw),'sha256':sha256(raw).hexdigest()} for name,raw in parents.items()},
        'catalog':[(str(item.path.relative_to(ROOT)),item.bytes,item.sha256) for item in catalog.files],
        'sources':pins,
    })).hexdigest()


def _definition_record(definition):
    dependencies=definition_closure(tuple(definition.conceptual_dependencies))
    reading=_FormulaCompactor(dependencies).compact(definition.template_source)
    source=re.sub(r'\bSum\(', 'BetaSum(',reading['defined_statement'])
    aliases={**DEFINITIONS,'BetaSum':replace(DEFINITIONS['Sum'],name='BetaSum')}
    exact,free=parse_formula_with_names(definition.template_source)
    parser=_LocalDefinedParser(source,aliases)
    parser.free=list(free)
    if parser.parse()!=exact or tuple(parser.free)!=free:
        _error('polynomial notation changed its exact conservative graph')
    return {'parameters':list(definition.parameters),'meaning':definition.summary,
        'expansion':source,'reviewed_definition_id':definition.stable_id,
        'reviewed_expansion_sha256':sha256(definition.template_source.encode()).hexdigest(),
        'exact_defined_expansion_equivalence_checked':True}


def _retained_syntax(state,selection):
    if (type(state) is not support.CandidateState or type(selection) is not support.SupportSelection
            or type(state.rows) is not tuple or len(state.rows)!=NEW_COUNT
            or any(type(row) is not TheoremSpec for row in state.rows)
            or state.sources!=support.MATH_SOURCE_PINS
            or state.specs_sha256!=support.NEW_SPECS_SHA256
            or support.closure._specs_digest(state.rows)!=state.specs_sha256
            or selection.owned!=state.rows or selection.current_support
            or len(selection.complete_specs)!=COMPLETE_COUNT
            or len(selection.parent_support)!=INHERITED_COUNT):
        _error('the retained polynomial syntax or inherited/new ownership changed')
    if type(selection.plan) is not support.closure.BottomLayerPlan:
        _error('the retained polynomial cone has no original typed dependency plan')
    specs=selection.complete_specs
    names=tuple(row.name for row in specs)
    owned={row.name for row in state.rows}
    if (len(set(names))!=COMPLETE_COUNT or set(selection.parent_support)!=set(names)-owned
            or len(set(selection.parent_support))!=INHERITED_COUNT
            or tuple(row.name for row in selection.plan.rows)!=names
            or not set(checkpoints.PRINCIPAL_ROOTS)<=owned):
        _error('the retained complete polynomial dependency inventory changed')
    known=set()
    edges=0
    for index,(row,planned) in enumerate(zip(specs,selection.plan.rows,strict=True)):
        if (type(row) is not TheoremSpec or planned.node_id!=index
                or planned.dependencies!=row.dependencies
                or planned.statement_sha256!=sha256(row.statement.encode()).hexdigest()
                or len(set(row.dependencies))!=len(row.dependencies)
                or not set(row.dependencies)<=known):
            _error('a retained proof edge, exact target, or topological position changed')
        known.add(row.name)
        edges+=len(row.dependencies)
    if edges!=selection.plan.dependency_edge_count:
        _error('the retained proof-edge count disagrees with its actual typed DAG')


def _research_evidence(corpus,report,state,selection):
    """Validate the live caller's display inputs, not reconstruct authority."""
    if (type(report) is not dict or set(report)!=REPORT_KEYS
            or report.get('schema')!=REPORT_SCHEMA
            or type(report.get('fresh_worker_count')) is not int or report['fresh_worker_count']!=8
            or report.get('polynomial_prerequisite_principals_checked') is not True
            or any(report.get(key) is not False for key in
                ('stored_receipt_is_proof_authority','published','alpha_admission_performed','stable_admission_performed'))
            or type(report.get('peak_rss_bytes')) is not int
            or not 0<report['peak_rss_bytes']<=1536*1024*1024):
        _error('incomplete or mislabelled live polynomial prerequisite report')
    _retained_syntax(state,selection)
    pin=checkpoints.require_final_inventory()
    if support.canonical(report['checkpoint'])!=support.canonical(checkpoints.expected_report(pin,state,selection)):
        _error('the polynomial display report differs from the exact whole-bundle contract')
    roots=report['principal_roots']
    if (type(roots) is not list or any(type(row) is not dict for row in roots)
            or tuple(row.get('name') for row in roots)!=checkpoints.PRINCIPAL_ROOTS):
        _error('the live polynomial report is missing an exact ordinary principal')
    for row in roots:
        expected=checkpoints.expected_root_report(pin,selection,row['name'])['principal_roots'][0]
        count=row.get('ordinary_certificate_nodes')
        if (type(count) is not int or not 1<count<=support.closure.DEFAULT_LAYERED_REPLAY_LIMITS.max_candidate_proof_occurrences
                or support.canonical(row)!=support.canonical({**expected,'ordinary_certificate_nodes':count})):
            _error('an exact ordinary polynomial certificate record changed')
    expected_novelty={'new_theorems':NEW_COUNT,'prior_theorems':3886,
        'new_specs_sha256':state.specs_sha256,'exact_statement_ast_duplicates':[],
        'exact_ast_novelty_checked':True}
    if support.canonical(report['novelty'])!=support.canonical(expected_novelty):
        _error('the complete Alpha-plus-G009 exact AST novelty audit is missing')
    if (type(corpus) is not dict or corpus.get('family_slug')!=SLUG
            or type(corpus.get('node_count')) is not int or corpus['node_count']!=NEW_COUNT
            or any(type(corpus.get(key)) is not int or corpus[key]!=0 for key in
                ('alpha_checked_use_node_count','alpha_enrolled_node_count','stable_admitted_node_count'))
            or corpus.get('proof_bundle_sha256')!=pin.sha256):
        _error('the polynomial reader changed proof identity or admission status')
    nodes=corpus.get('nodes')
    if (type(nodes) is not list or any(type(node) is not dict for node in nodes)
            or tuple(node.get('name') for node in nodes)!=tuple(row.name for row in state.rows)):
        _error('the polynomial reader lost or reordered its exact 85 rows')
    tags={row.name:f'{TAG_PREFIX}{index:04X}' for index,row in enumerate(state.rows,1)}
    if (corpus.get('tags')!=tags or corpus.get('root_names')!=list(checkpoints.PRINCIPAL_ROOTS)
            or tags.get(ROOT_NAME)!='PQ0055'):
        _error('the polynomial reader changed its six roots or stable hexadecimal PQ routes')
    positions={row.name:row.node_id for row in selection.plan.rows}
    for spec,node in zip(state.rows,nodes,strict=True):
        if (node.get('id')!=tags[spec.name] or node.get('statement')!=spec.statement
                or node.get('script')!=list(spec.script) or node.get('dependencies')!=list(spec.dependencies)
                or node.get('statement_sha256')!=sha256(spec.statement.encode()).hexdigest()
                or type(node.get('proof_bundle_node_id')) is not int
                or node['proof_bundle_node_id']!=positions[spec.name]
                or any(node.get(key) is not False for key in ('alpha_checked_use','admitted_to_alpha','stable_member'))):
            _error('the polynomial reader changed an exact theorem, proof position or membership')
        reading=node.get('defined')
        if (type(reading) is not dict or reading.get('exact_ast_equivalence') is not True
                or reading.get('expanded_statement_sha256')!=node['statement_sha256']
                or type(reading.get('defined_statement')) is not str):
            _error('the polynomial reader has no exact conservative displayed statement')
        parser=_LocalDefinedParser(reading['defined_statement'],DEFINITIONS)
        if parser.parse()!=_closed_formula(spec.statement) or parser.free:
            _error('a displayed polynomial theorem changed its exact closed formula')
    return next(node for node in nodes if node['name']==ROOT_NAME),pin


def _parent_context(parents):
    original=_document(parents['campaign.json'])
    graph=_document(parents['definitions.json'])
    audit=_document(parents['dag-audit.json'])
    meta=original.get('meta',{})
    nodes=original.get('nodes',())
    if (original.get('schema')!='constructive-grand-campaign-v1'
            or meta.get('current_alpha_version')!='v31' or meta.get('current_alpha_checked_use_count')!=3796
            or meta.get('goal_count')!=120 or len(nodes)!=144
            or len({node.get('id') for node in nodes})!=144):
        _error('the immutable parent atlas has the wrong goal or Alpha inventory')
    by_id={node['id']:node for node in nodes}
    g009,g091=by_id['G009'],by_id['G091']
    release=original.get('ambitious_boundaries',{}).get('alpha_v31_edition',{})
    if (g009.get('status')!='available' or g009.get('research_proof_closed') is not True
            or g009.get('evidence',{}).get('full_G009_finite_coded_contract_proved') is not True
            or g091.get('status')!='open' or g091.get('family')!='F10'
            or release.get('catalog_sha256')!=CATALOG_SHA256
            or release.get('checked_use_count')!=3796 or release.get('stable_closed_count')!=432
            or len(original.get('definitions',{}))!=467):
        _error('the G009 completion, open G091 boundary, or current Alpha identity changed')
    milestone,edges=_milestone_dag(original)
    definitions,reviewed,de,re,usage,statement,declared=_definition_dags(original,graph)
    expected={
        'alpha_version':'v31','catalog_sha256':CATALOG_SHA256,
        'theorem_count':3796,'theorem_edge_count':12248,
        'milestone_count':len(milestone),'milestone_proof_edge_count':edges,
        'milestone_dag_sha256':_projection_digest(milestone),
        'definition_count':len(definitions),'definition_edge_count':de,
        'definition_dag_sha256':_projection_digest(definitions),
        'reviewed_definition_count':len(reviewed),'reviewed_definition_edge_count':re,
        'reviewed_definition_dag_sha256':_projection_digest(reviewed),
        'milestone_usage_edge_count':usage,'statement_usage_edge_count':statement,
        'declared_notation_edge_count':declared,'campaign_snapshot_sha256':_digest(original),
    }
    if (any(support.canonical(audit.get(key))!=support.canonical(value) for key,value in expected.items())
            or graph.get('reviewed_definition_count')!=383 or graph.get('reviewed_definition_edge_count')!=825
            or not re_full_digest(audit.get('theorem_dag_sha256'))
            or audit.get('research_proof_dag',{}).get('theorem_count')!=461
            or audit.get('research_proof_dag',{}).get('new_theorem_count')!=90):
        _error('the literal parent atlas audit disagrees with its actual milestone/definition DAGs')
    return original,graph,audit


def re_full_digest(value):
    return type(value) is str and re.fullmatch(r'[0-9a-f]{64}',value) is not None


def _project(original,corpus,root,pin,report):
    """Pure display projection of validated inputs; fixtures here are not proofs."""
    previous={node['id']:node for node in original['nodes']}
    if (len(previous)!=144 or original['meta'].get('goal_count')!=120
            or previous['G091'].get('status')!='open' or previous['G091'].get('family')!='F10'
            or previous['G009'].get('status')!='available'
            or previous['G009'].get('research_proof_closed') is not True):
        _error('prerequisite progress must extend the actual open-G091, closed-G009 parent')
    result=deepcopy(original)
    if any(key in result['meta'] for key in META_ADDITIONS):
        _error('polynomial prerequisite metadata already exists in the immutable parent')
    result['meta'].update(META_ADDITIONS)
    for definition in POLYNOMIAL_DIVISION_DEFINITIONS:
        if definition.name in result['definitions']:
            _error('a polynomial graph shadows inherited planning or reviewed notation')
        result['definitions'][definition.name]=_definition_record(definition)
    routes=[{'route':SLUG,'label':name,'tag':corpus['tags'][name]}
            for name in checkpoints.PRINCIPAL_ROOTS]
    goal=next(row for row in result['nodes'] if row['id']=='G091')
    if 'polynomial_prerequisite_progress' in goal:
        _error('the new prerequisite progress shadows a previous record')
    progress={
        'scope':'independently_checked_polynomial_prerequisites_only',
        'prerequisite_proof_closed':True,'full_G091_proved':False,
        'alpha_enrolled':False,'checked_use':False,'stable_member':False,
        'new_theorem_count':NEW_COUNT,'inherited_alpha_theorem_count':INHERITED_COUNT,
        'complete_cone_theorem_count':COMPLETE_COUNT,'ordinary_principal_count':6,
        'principal_roots':deepcopy(report['principal_roots']),
        'bundle_path':pin.path,'bundle_sha256':pin.sha256,'bundle_nodes':pin.nodes,
        'bundle_dependencies':pin.edges,'original_ha_checked':True,
        'same_bytes_compiled_lean_checked':True,
        'representative_theorem_name':ROOT_NAME,'representative_statement_sha256':root['statement_sha256'],
        'representative_proof_tag':root['id'],'proof_routes':routes,
        'domain':'D04','family':'F10','summary':REFINEMENT,
        'remaining_obligations':list(REMAINING),
    }
    goal['polynomial_prerequisite_progress']=progress
    goal['why']=goal.get('why','')+'\n\n'+REFINEMENT
    goal['definition_refs']=list(dict.fromkeys((*goal.get('definition_refs',()),
        *(definition.name for definition in POLYNOMIAL_DIVISION_DEFINITIONS))))
    goal.setdefault('additional_checked_chapters',[]).append({
        'slug':SLUG,'title':corpus['family_title'],'theorem_count':NEW_COUNT,
        'closes_full_milestone':False,'full_G091_proved':False,
        'alpha_checked_use':False,'stable_member':False,
        'authority':'local_research_prerequisites_not_alpha_or_stable',
        'proof_routes':routes,
    })
    goal['references']=list(dict.fromkeys((*goal.get('references',()),'S85','S86','S87')))
    sources=(
        {'id':'S85','kind':'independent_proof_artifact','label':'Actual polynomial prerequisite dependency bundle','path':pin.path},
        {'id':'S86','kind':'independent_closure_record','label':'Fresh original HA, compiled Lean and six polynomial prerequisite certificates','path':f'book/_static/{READER_PACKAGE}/proof-audit.json'},
        {'id':'S87','kind':'research_contract','label':'Polynomial prerequisite contracts and the still-open G091 boundary','path':RFC_PATH},
        {'id':'S88','kind':'historical_presentation_parent','label':'Unchanged G009-complete atlas before polynomial prerequisites','path':'book/_static/constructive-g009-explorer/grand-campaign/campaign.json'},
    )
    if {source['id'] for source in sources}&{source['id'] for source in result['sources']}:
        _error('a polynomial source reused an inherited provenance identifier')
    result['sources'].extend(sources)
    key='g091_polynomial_prerequisite_progress'
    if key in result['ambitious_boundaries']:
        _error('a polynomial boundary shadows an inherited source record')
    result['ambitious_boundaries'][key]={
        'full_G091_proved':False,'prerequisite_proof_closed':True,
        'new_theorem_count':NEW_COUNT,'inherited_alpha_theorem_count':INHERITED_COUNT,
        'complete_cone_theorem_count':COMPLETE_COUNT,'ordinary_principal_count':6,
        'bundle_sha256':pin.sha256,'alpha_admission_performed':False,
        'stable_admission_performed':False,'current_alpha_unchanged':True,
        'G009_research_completion_unchanged':True,'all_goal_statuses_unchanged':True,
        'definitions_are_not_proof_premises':True,
        'remaining_obligations':list(REMAINING),
    }
    for node in result['nodes']:
        prior=previous[node['id']]
        if node['status']!=prior['status'] or node['statement']!=prior['statement'] or node['deps']!=prior['deps']:
            _error('polynomial prerequisites changed a goal status, statement or proof dependency')
        if node['id']!='G091' and node!=prior:
            _error('polynomial prerequisites changed an unrelated atlas node')
        if node.get('evidence')!=prior.get('evidence'):
            _error('polynomial prerequisites changed inherited milestone authority')
    for name,value in original['ambitious_boundaries'].items():
        if result['ambitious_boundaries'][name]!=value:
            _error('polynomial prerequisites changed an inherited release boundary')
    return result


def _audit(original,parent_graph,parent_audit,campaign,graph,selection,pin):
    milestone,edges=_milestone_dag(campaign)
    definitions,reviewed,de,re,usage,statement,declared=_definition_dags(campaign,graph)
    if (len(reviewed)!=REVIEWED_COUNT or re!=REVIEWED_EDGES
            or _projection_digest(milestone)!=parent_audit['milestone_dag_sha256']
            or edges!=parent_audit['milestone_proof_edge_count']):
        _error('the exact new definition inventory or preserved milestone proof DAG changed')
    old_reviewed={row['id']:row for row in parent_graph['reviewed_definitions']}
    new_reviewed={row['id']:row for row in graph['reviewed_definitions']}
    if any(new_reviewed.get(name)!=row for name,row in old_reviewed.items()):
        _error('a new notation graph changed an inherited reviewed definition')
    if any(campaign['definitions'].get(name)!=value for name,value in original['definitions'].items()):
        _error('a new notation graph changed an inherited blueprint expansion')
    data=deepcopy(parent_audit)
    data.update(
        milestone_count=len(milestone),milestone_proof_edge_count=edges,
        milestone_dag_sha256=_projection_digest(milestone),
        definition_count=len(definitions),definition_edge_count=de,
        definition_dag_sha256=_projection_digest(definitions),
        reviewed_definition_count=len(reviewed),reviewed_definition_edge_count=re,
        reviewed_definition_dag_sha256=_projection_digest(reviewed),
        milestone_usage_edge_count=usage,statement_usage_edge_count=statement,
        declared_notation_edge_count=declared,campaign_snapshot_sha256=_digest(campaign),
    )
    data['inherited_proof_dag_boundary']={
        'source':'book/_static/constructive-g009-explorer/grand-campaign/dag-audit.json',
        **PARENT_PINS['dag-audit.json'],
        'alpha_proof_dag_recomputed_here':False,'G009_proof_dag_recomputed_here':False,
        'literal_parent_proof_records_preserved':True,
        'current_milestone_and_definition_dags_recomputed':True,
        'saved_parent_audit_is_new_proof_authority':False,
    }
    data['polynomial_prerequisite_proof_dag']={
        'purpose':'Separate same-live checked prerequisite cone; not G091 closure or Alpha admission',
        'theorem_count':COMPLETE_COUNT,'new_theorem_count':NEW_COUNT,
        'inherited_alpha_theorem_count':INHERITED_COUNT,
        'ordered_names_sha256':selection.plan.ordered_names_sha256,
        'dependency_edges':selection.plan.dependency_edge_count,
        'bundle_sha256':pin.sha256,'all_theorem_bodies_original_ha_checked':True,
        'same_bytes_compiled_lean_checked':True,'ordinary_principal_count':6,
        'full_G091_proved':False,'alpha_admission_performed':False,
        'stable_admission_performed':False,'notation_edges_are_proof_premises':False,
    }
    return data


def _once(source,before,after):
    if source.count(before)!=1:
        _error('the immutable G009 atlas navigation or display function changed')
    return source.replace(before,after,1)


def _html(source,campaign,graph):
    # The parent is already nested and its initial header links are correct.
    # Only the own-package exception changes; old G009 becomes a sibling.
    for name,key,compatible in (('COMPILED_DEFINITIONS','compatible_reviewed_matches',True),
                                ('INCOMPATIBLE_DEFINITIONS','incompatible_reviewed_matches',False)):
        rows=[{**row,'route':graph.get('definition_page_overrides',{}).get(
            row['reviewed_id'],{}).get('route',row['route'])} for row in graph[key]]
        source,count=re.subn(r'      var '+name+r' = \{.*?\n      \};',
            lambda _match:_table_source(name,rows,compatible=compatible),source,count=1,flags=re.S)
        if count!=1:
            _error('the inherited atlas definition table changed')
    marker='        var currentFamilies = '
    start=source.find(marker)
    end=source.find(';\n',start)
    if start<0 or end<0 or source.count(marker)!=1:
        _error('the inherited atlas family dispatcher changed')
    routes=json.loads(source[start+len(marker):end])
    if SLUG in routes or routes.get('multiplicative-convolution')!='constructive-g009-explorer':
        _error('the new family shadows an inherited research route')
    routes[SLUG]=READER_PACKAGE
    source=source[:start]+marker+json.dumps(routes,sort_keys=True)+source[end:]
    source=_once(source,
        '        if (route === "multiplicative-convolution") return "../multiplicative-convolution/explorer/defined/";',
        f'        if (route === "{SLUG}") return "../{SLUG}/explorer/defined/";')
    source=_once(source,
        '            include(descriptor, "Additional checked chapter — inspect the exact statement");',
        f'            include(descriptor, chapter.slug === "{SLUG}" && chapter.closes_full_milestone === false ?\n'
        '              "Verified polynomial prerequisite — G091 remains open; not Alpha/Stable" :\n'
        '              "Additional checked chapter — inspect the exact statement");')
    marker='      function statusCaveat(node) {\n'
    source=_once(source,marker,marker+
        '        if (node.id === "G091" && node.status === "open" && node.polynomial_prerequisite_progress &&\n'
        '            node.polynomial_prerequisite_progress.prerequisite_proof_closed === true &&\n'
        '            node.polynomial_prerequisite_progress.full_G091_proved === false &&\n'
        '            node.polynomial_prerequisite_progress.checked_use === false &&\n'
        '            node.polynomial_prerequisite_progress.alpha_enrolled === false &&\n'
        '            node.polynomial_prerequisite_progress.stable_member === false) {\n'
        '          return '+json.dumps(REFINEMENT,ensure_ascii=False)+';\n'
        '        }\n')
    if re.search(r'^\s*G091:',source,flags=re.M):
        _error('an open G091 goal acquired a falsely complete proof-root descriptor')
    snapshot=json.dumps(campaign,ensure_ascii=False,allow_nan=False,separators=(',',':'))
    if '</script' in snapshot.lower() or len(snapshot.encode())>MAX_CAMPAIGN_BYTES:
        _error('unsafe or oversized embedded prerequisite campaign')
    return _expected(source,snapshot)[1].encode()


def build_files_for_verified_reader(corpus,report,state,selection):
    """Return four display documents only after the caller's live eight gates."""
    binding=source_binding()
    root,pin=_research_evidence(corpus,report,state,selection)
    parents=parent_files()
    original,parent_graph,parent_audit=_parent_context(parents)
    campaign=_project(original,corpus,root,pin,report)
    graph=build_definition_graph(campaign)
    audit=_audit(original,parent_graph,parent_audit,campaign,graph,selection,pin)
    result={'campaign.json':_json(campaign),'definitions.json':_json(graph),
            'dag-audit.json':_json(audit),'index.html':_html(parents['index.html'].decode(),campaign,graph)}
    if parent_files()!=parents or source_binding()!=binding:
        _error('the immutable parent or formatting sources changed during prerequisite rendering')
    return result


__all__=('source_binding','build_files_for_verified_reader')
