"""Pure G009 research projection for the same-live verified reader build.

No standalone entrypoint, receipt input, catalogue mutation, or admission.
The caller first completes all eight fresh proof workers. The unchanged
Alpha DAG and the separately checked research cone keep distinct authority.
"""

from copy import deepcopy
from dataclasses import asdict, replace
from hashlib import sha256
import json
from pathlib import Path
import re

import constructive_g009_support as support
import constructive_g009_checkpoints as checkpoints
from constructive_g009_definitions import (
    ALL_CONSTRUCTIVE_DEFINITIONS_BY_NAME as DEFINITIONS, G009_DEFINITIONS,
    definition_closure,
)
from constructive_g009_definition_graph import build_definition_graph
from constructive_formula_compactor import _FormulaCompactor, _LocalDefinedParser
from extend_constructive_second_wave_campaign import _table_source
from peano_catalog_shards import load_catalog, verify_catalog_bindings
from sync_constructive_grand_campaign import MAX_CAMPAIGN_BYTES, _expected, validate_campaign_dags
from peano_lab.kernel.formulas import parse_formula_with_names
from peano_lab.library.theorems import _closed_formula


ROOT = support.ROOT
PARENT_NAME = 'constructive-completed-lower-campaign-v31'
PARENT = ROOT/'book/_static'/PARENT_NAME
# Literal inputs from the genuinely installed and deployed v31 publication.
# These identities grant no G009 proof or admission authority.
PARENT_PINS = {
    "campaign.json": {
        "bytes": 604401,
        "sha256": "dbf0c778d26c82b7495290e9dfc8bc7d02de0c8a0ea3ba71d55378d609251691"
    },
    "dag-audit.json": {
        "bytes": 968,
        "sha256": "48f548cb20523c8199aa6badec80f5cfd60947622b5ae9b68625ea46c23a722b"
    },
    "definitions.json": {
        "bytes": 1408443,
        "sha256": "99edf2afdf124d89f1415e63d021da991bc43809b7c7fc0c2cc9a78cc7b88b92"
    },
    "index.html": {
        "bytes": 665366,
        "sha256": "158bbcb81028309c74f1171587b6162107e4cbd85463c62b79170f1c02a15d20"
    }
}
SLUG = 'multiplicative-convolution'
READER_PACKAGE = 'constructive-g009-explorer'
ROOT_NAME = 'dirichlet_convolution_multiplicative_exists_unique'
CATALOG_SHA256 = '6c9ebfb3c37e42aefab200b710f78e7693dc5826c80f053544deea41caf44aab'
CATALOG_PATH = 'artifacts/peano-library/alpha/catalog-v31.json'
INHERITED_COMPONENTS = (
    'dirichlet_convolution_table_exists_extensionally_unique',
    'dirichlet_convolution_associative',
    'dirichlet_delta_unit_exists',
    'dirichlet_inverse_positive_criterion',
)
REFINEMENT = (
    'Full G009 is proved for actual finite signed arithmetic-function tables. '
    'Previously admitted construction, associativity, delta identity and the exact '
    'signed-unit inverse criterion are completed by normalized coprime multiplicative '
    'closure on every nonempty positive prefix, with the inclusive bound m*n<=N. '
    'All tables, divisor pairs, Cartesian products and support maps are constructed. '
    'Zero-index values and physical table encodings remain unrestricted. '
    'This is a complete local research proof, not an Alpha or Stable admission.'
)


def _json(value):
    data = (json.dumps(value,ensure_ascii=False,allow_nan=False,sort_keys=True,indent=2)+'\n').encode()
    if len(data) > MAX_CAMPAIGN_BYTES:
        raise support.G009Error('G009 campaign exceeds the unchanged8MiB document bound')
    return data


def parent_files():
    if set(PARENT_PINS) != {'campaign.json','definitions.json','dag-audit.json','index.html'}:
        raise support.G009Error('actual v31 campaign publication pins are not registered')
    result = {}
    for name,pin in PARENT_PINS.items():
        if (type(pin) is not dict or set(pin) != {'bytes','sha256'} or
                type(pin['bytes']) is not int or not 0 < pin['bytes'] <= MAX_CAMPAIGN_BYTES):
            raise support.G009Error('invalid actual v31 campaign pin')
        support.check_pin(support.FilePin(name,pin['bytes'],pin['sha256']),PARENT,MAX_CAMPAIGN_BYTES)
        raw = support.bounded_bytes(PARENT/name,MAX_CAMPAIGN_BYTES)
        if len(raw) != pin['bytes'] or sha256(raw).hexdigest() != pin['sha256']:
            raise support.G009Error('actual campaign input changed while reading')
        result[name] = raw
    return result


def source_binding():
    """Fresh bounded byte identity for the caller's pre/post render guards."""
    parents = parent_files()
    catalog = verify_catalog_bindings(ROOT/CATALOG_PATH,expected_sha256=CATALOG_SHA256)
    sources = (
        'scripts/sync_constructive_grand_campaign.py',
        'scripts/extend_constructive_second_wave_campaign.py',
        'scripts/constructive_formula_compactor.py',
        'scripts/constructive_definition_graph.py',
        'scripts/constructive_dirichlet_inverse_definitions.py',
        'scripts/constructive_dirichlet_inverse_definition_graph.py',
        'scripts/peano_catalog_shards.py',
    )
    fingerprints = []
    for path in sources:
        raw = support.bounded_bytes(ROOT/path,support.MAX_SOURCE_BYTES)
        fingerprints.append((path,len(raw),sha256(raw).hexdigest()))
    return sha256(support.canonical({
        'parents':{name:{'bytes':len(raw),'sha256':sha256(raw).hexdigest()} for name,raw in parents.items()},
        'catalog':[(str(item.path.relative_to(ROOT)),item.bytes,item.sha256) for item in catalog.files],
        'sources':fingerprints,
    })).hexdigest()


def _definition_record(definition):
    dependencies = definition_closure(tuple(definition.conceptual_dependencies))
    reading = _FormulaCompactor(dependencies).compact(definition.template_source)
    source = re.sub(r'\bSum\(', 'BetaSum(',reading['defined_statement'])
    aliases = {**DEFINITIONS,'BetaSum':replace(DEFINITIONS['Sum'],name='BetaSum')}
    exact,free = parse_formula_with_names(definition.template_source)
    parser = _LocalDefinedParser(source,aliases)
    parser.free = list(free)
    if parser.parse() != exact or tuple(parser.free) != free:
        raise support.G009Error('G009 campaign definition changed its exact conservative graph')
    return {'parameters':list(definition.parameters),'meaning':definition.summary,
            'expansion':source,'reviewed_definition_id':definition.stable_id,
            'reviewed_expansion_sha256':sha256(definition.template_source.encode()).hexdigest(),
            'exact_defined_expansion_equivalence_checked':True}


def _research_evidence(corpus,report,state,selection):
    if (type(state) is not support.CandidateState or type(selection) is not support.SupportSelection or
            len(state.rows) != 90 or state.rows != selection.owned or selection.current_support or
            len(selection.complete_specs) != 461 or len(selection.parent_support) != 371 or
            report.get('fresh_worker_count') != 8 or
            report.get('schema') != 'peano-g009-local-research-checkpoint-v1' or
            report.get('multiplicative_convolution_principals_checked') is not True or
            any(report.get(key) is not False for key in (
                'stored_receipt_is_proof_authority','alpha_admission_performed',
                'stable_admission_performed','published'))):
        raise support.G009Error('incomplete or mislabelled G009 research projection')
    pin = checkpoints.require_final_inventory()
    if support.canonical(report.get('checkpoint')) != support.canonical(
            checkpoints.expected_report(pin,state,selection)):
        raise support.G009Error('research projection differs from the exact full bundle inventory')
    roots = report.get('principal_roots')
    if (type(roots) is not list or tuple(row.get('name') for row in roots) != checkpoints.PRINCIPAL_ROOTS):
        raise support.G009Error('research projection is missing an ordinary principal')
    for row in roots:
        expected = checkpoints.expected_root_report(pin,selection,row['name'])['principal_roots'][0]
        count = row.get('ordinary_certificate_nodes')
        if (type(count) is not int or not 1 < count <=
                support.closure.DEFAULT_LAYERED_REPLAY_LIMITS.max_candidate_proof_occurrences or
                row != {**expected,'ordinary_certificate_nodes':count}):
            raise support.G009Error('research ordinary certificate record changed')
    novelty = report.get('novelty')
    if novelty != {'new_theorems':90,'prior_theorems':3796,'new_specs_sha256':state.specs_sha256,
                   'exact_statement_ast_duplicates':[],'exact_ast_novelty_checked':True}:
        raise support.G009Error('the entire G009 novelty audit is missing')
    if (corpus.get('family_slug') != SLUG or corpus.get('node_count') != 90 or
            corpus.get('alpha_checked_use_node_count') != 0 or
            corpus.get('alpha_enrolled_node_count') != 0 or corpus.get('stable_admitted_node_count') != 0 or
            corpus.get('proof_bundle_sha256') != pin.sha256):
        raise support.G009Error('the research reader falsely changes admission or proof identity')
    by_name = {row['name']:row for row in corpus['nodes']}
    if len(by_name) != 90 or tuple(by_name) != tuple(row.name for row in state.rows):
        raise support.G009Error('research reader lost or reordered its exact ninety rows')
    tags = {row.name:f'MX{index:04X}' for index,row in enumerate(state.rows,1)}
    if (corpus.get('tags') != tags or
            corpus.get('root_names') != list(checkpoints.PRINCIPAL_ROOTS) or
            any(node.get('id') != tags[name] for name,node in by_name.items())):
        raise support.G009Error('research reader changed a stable tag or the exact six principal routes')
    positions = {row.name:row.node_id for row in selection.plan.rows}
    for spec in state.rows:
        node = by_name[spec.name]
        if (node['statement'] != spec.statement or node['script'] != list(spec.script) or
                node['dependencies'] != list(spec.dependencies) or
                node['statement_sha256'] != sha256(spec.statement.encode()).hexdigest() or
                node['proof_bundle_node_id'] != positions[spec.name] or
                node.get('alpha_checked_use') is not False or
                node.get('admitted_to_alpha') is not False or node.get('stable_member') is not False):
            raise support.G009Error('research reader changed an exact theorem or membership')
        reading = node.get('defined',{})
        if (reading.get('exact_ast_equivalence') is not True or
                reading.get('expanded_statement_sha256') != node['statement_sha256']):
            raise support.G009Error('research reader lacks exact defined-statement identity')
        parser = _LocalDefinedParser(reading['defined_statement'],DEFINITIONS)
        if parser.parse() != _closed_formula(spec.statement) or parser.free:
            raise support.G009Error('a research theorem changed under displayed conservative notation')
    root = by_name[ROOT_NAME]
    parser = _LocalDefinedParser(root['defined']['defined_statement'],DEFINITIONS)
    if parser.parse() != _closed_formula(root['statement']) or parser.free:
        raise support.G009Error('G009 displayed endpoint is not the exact closed formula')
    return root,pin


def _project(original,catalog,corpus,root,pin,report):
    """Pure formatting of validated evidence; this function grants no authority."""
    if (original.get('schema') != 'constructive-grand-campaign-v1' or
            original.get('meta',{}).get('current_alpha_version') != 'v31' or
            original['meta'].get('current_alpha_checked_use_count') != 3796 or
            len(original.get('nodes',())) != 144 or original['meta'].get('goal_count') != 120 or
            catalog.get('schema') != 'peano-library-alpha-snapshot-v31' or
            catalog.get('checked_use_count') != 3796):
        raise support.G009Error('G009 projection has the wrong current immutable parent')
    old_nodes = {node['id']:node for node in original['nodes']}
    if old_nodes['G009']['status'] != 'open' or old_nodes['G091']['status'] != 'open':
        raise support.G009Error('the original v31 milestone boundary changed')
    by_name = {row['name']:row for row in catalog['theorems']}
    if len(by_name) != 3796 or set(row['name'] for row in corpus['nodes'])&set(by_name):
        raise support.G009Error('new research rows collide with current Alpha admission')
    components = []
    for name in INHERITED_COMPONENTS:
        row = by_name.get(name)
        if row is None or row.get('checked_use') is not True:
            raise support.G009Error('a required admitted G009 component is missing')
        components.append({'name':name,'statement_sha256':row['statement_sha256'],
                           'alpha_version':'v31','checked_use':True})
    result = deepcopy(original)
    result['meta'].update(g009_research_new_theorem_count=90,
        g009_research_full_goal_proved=True,g009_research_alpha_admission=False,
        g009_research_release_date='2026-08-30')
    for definition in G009_DEFINITIONS:
        if definition.name in result['definitions']:
            raise support.G009Error('a new G009 definition shadows planning or reviewed notation')
        result['definitions'][definition.name] = _definition_record(definition)
    goal = next(row for row in result['nodes'] if row['id'] == 'G009')
    goal['historical_alpha_v31_evidence'] = deepcopy(goal['evidence'])
    goal['historical_planned_statement'] = goal['statement']
    goal.update(status='available',research_proof_closed=True,
                statement=root['defined']['defined_statement'],why=REFINEMENT,
                representation_refinement=REFINEMENT,remaining_obligations=[])
    used = set(root['defined']['statement_definition_uses'])
    goal['definition_refs'] = list(dict.fromkeys((*goal.get('definition_refs',()),
        *(definition.name for definition in DEFINITIONS.values() if definition.stable_id in used))))
    routes = [{'route':SLUG,'label':name,'tag':corpus['tags'][name]}
              for name in corpus['root_names']]
    goal['evidence'] = {
        'implementation':'independently_closed_local_research','release_status':'local_closed',
        'checked_use':False,'alpha_enrolled':False,'stable_member':False,
        'local_checkpoint_verified':True,'full_empty_context_closure':True,
        'independent_lean_bundle_verified':True,'research_theorem_name':ROOT_NAME,
        'research_theorem_statement_sha256':root['statement_sha256'],
        'research_principal_roots':deepcopy(report['principal_roots']),
        'research_new_theorem_count':90,'inherited_contract_components':components,
        'checked_theorem_names':[row['name'] for row in components],
        'bundle_path':pin.path,'bundle_sha256':pin.sha256,'bundle_nodes':pin.nodes,
        'bundle_dependencies':pin.edges,'bundle_node_id':root['proof_bundle_node_id'],
        'route':SLUG+'/','proof_tag':root['id'],'proof_routes':routes,
        'multiplicative_convolution_closure_proved':True,'full_G009_finite_coded_contract_proved':True,
        'unrestricted_zero_values':True,'positive_represented_value_uniqueness':True,
        'normalization_at_one_for_multiplicativity':'+1 only',
        'inverse_criterion_includes_both_signed_units':True,
        'inverse_multiplicativity_claimed':False,
        'original_full_contract':'PLAN/14_constructive_number_theory_grand_campaign.md',
    }
    goal.setdefault('additional_checked_chapters',[]).append({
        'slug':SLUG,'title':corpus['family_title'],'theorem_count':90,
        'proof_routes':routes,'closes_full_milestone':True,
        'authority':'local_research_not_alpha_admission'})
    goal['references'] = list(dict.fromkeys((*goal.get('references',()),'S81','S82','S83')))
    sources = [
        {'id':'S81','kind':'independent_proof_artifact','label':'G009 complete signed multiplicative convolution proof bundle','path':pin.path},
        {'id':'S82','kind':'independent_closure_record','label':'Fresh original HA, compiled Lean and six ordinary G009 certificates','path':'book/_static/constructive-g009-explorer/proof-audit.json'},
        {'id':'S83','kind':'research_contract','label':'Exact finite signed G009 representation and admission boundary','path':'research/arithmetic-library/g009-multiplicative-convolution-rfc-v1.md'},
        {'id':'S84','kind':'historical_presentation_parent','label':'Unchanged v31 atlas before local G009 completion','path':'book/_static/'+PARENT_NAME+'/campaign.json'},
    ]
    if {row['id'] for row in sources}&{row['id'] for row in result['sources']}:
        raise support.G009Error('G009 reused a historical provenance identifier')
    result['sources'].extend(sources)
    result['ambitious_boundaries']['g009_local_research_completion'] = {
        'full_finite_coded_contract_proved':True,'new_theorem_count':90,
        'inherited_theorem_count':371,'complete_cone_theorem_count':461,
        'ordinary_principal_count':6,'bundle_sha256':pin.sha256,
        'current_alpha_unchanged':True,'stable_unchanged':True,
        'first_admission_unchanged':True,'historical_v31_snapshot_unchanged':True,
        'alpha_admission_performed':False,'definitions_are_not_proofs':True,
        'G091_general_prime_power_fields':'open'}
    for node in result['nodes']:
        if node['id'] != 'G009' and node != old_nodes[node['id']]:
            raise support.G009Error('G009 changed an unrelated campaign node')
    if result['ambitious_boundaries']['alpha_v31_edition'] != original['ambitious_boundaries']['alpha_v31_edition']:
        raise support.G009Error('G009 silently changed current Alpha authority')
    return result


def _nested_navigation(source):
    """Keep initial and configured header links valid in the nested reader.

    The two initial flagship links use their intended public URLs so they
    work in both layouts before JavaScript runs. configure() then installs
    the actual relative raw/deployed routes through the existing dispatcher.
    The home link is relative to this reader in either layout.
    """
    revision = CATALOG_SHA256[:12]
    public = 'https://bnaskrecki.faculty.wmi.amu.edu.pl/proofs/'
    replacements = (
        ('<a href="../constructive-frontier-explorer/index.html" data-proof-home>',
         '<a href="../index.html?v='+revision+'" data-proof-home>'),
        ('<a href="../pa-proof-explorer/defined/index.html" data-proof-quadratic>',
         '<a href="'+public+'quadratic-reciprocity/explorer/defined/index.html?v='+revision+'" data-proof-quadratic>'),
        ('<a href="../bertrand-proof-explorer/defined/index.html" data-proof-bertrand>',
         '<a href="'+public+'bertrand-postulate/explorer/defined/index.html?v='+revision+'" data-proof-bertrand>'),
        ('document.querySelector("[data-proof-home]").setAttribute("href",\n'
         '          /\\/proofs\\/grand-campaign(?:\\/|$)/.test(window.location.pathname || "") ? "../index.html" :\n'
         '            "../constructive-frontier-explorer/index.html");',
         'document.querySelector("[data-proof-home]").setAttribute("href", proofHref("../index.html"));'),
        ('explorerBase("quadratic-reciprocity") + "index.html");',
         'proofHref(explorerBase("quadratic-reciprocity") + "index.html"));'),
        ('explorerBase("bertrand-postulate") + "index.html");',
         'proofHref(explorerBase("bertrand-postulate") + "index.html"));'),
    )
    for before,after in replacements:
        if source.count(before) != 1:
            raise support.G009Error('the inherited atlas header navigation changed')
        source = source.replace(before,after,1)
    return source


def _html(source,campaign,graph):
    source = _nested_navigation(source)
    for name,key,compatible in (('COMPILED_DEFINITIONS','compatible_reviewed_matches',True),
                                ('INCOMPATIBLE_DEFINITIONS','incompatible_reviewed_matches',False)):
        rows = [{**row,'route':graph.get('definition_page_overrides',{}).get(
                    row['reviewed_id'],{}).get('route',row['route'])} for row in graph[key]]
        source,count = re.subn(r'      var '+name+r' = \{.*?\n      \};',
            lambda match:_table_source(name,rows,compatible=compatible),source,count=1,flags=re.S)
        if count != 1:
            raise support.G009Error('the inherited atlas definition table changed')
    goal = next(row for row in campaign['nodes'] if row['id'] == 'G009')
    marker = '      var PROOF_ROOTS = {\n'
    if source.count(marker) != 1 or re.search(r'^\s*G009:',source,flags=re.M):
        raise support.G009Error('the inherited G009 proof-root route is ambiguous')
    descriptor = '        G009: { route: '+json.dumps(SLUG)+', label: "Full finite signed G009", tag: '+json.dumps(goal['evidence']['proof_tag'])+' },\n'
    source = source.replace(marker,marker+descriptor,1)
    marker = '        var currentFamilies = '
    start = source.find(marker)
    end = source.find(';\n',start)
    if start < 0 or end < 0 or source.count(marker) != 1:
        raise support.G009Error('the current atlas route dispatcher changed')
    routes = json.loads(source[start+len(marker):end])
    if SLUG in routes:
        raise support.G009Error('the new G009 route already shadows an atlas route')
    routes[SLUG] = READER_PACKAGE
    source = source[:start]+marker+json.dumps(routes,sort_keys=True)+source[end:]
    # This atlas is nested inside the new raw reader package, unlike the
    # historical sibling atlas directory. Public /proofs routes stay intact.
    old_return = '        return "../" + directory + "/" + route + "/explorer/defined/";'
    if source.count(old_return) != 1:
        raise support.G009Error('the exact raw atlas route return changed')
    source = source.replace(old_return,
        '        if (route === "'+SLUG+'") return "../'+SLUG+'/explorer/defined/";\n'
        '        return "../../" + directory + "/" + route + "/explorer/defined/";',1)
    marker = '      function proved(node) {\n'
    guard = (
        '      function localResearchProved(node) {\n'
        '        var evidence = node && node.evidence;\n'
        '        return !!node && node.id === "G009" && node.status === "available" && node.research_proof_closed === true &&\n'
        '          !!evidence && evidence.local_checkpoint_verified === true && evidence.full_empty_context_closure === true &&\n'
        '          evidence.independent_lean_bundle_verified === true && evidence.full_G009_finite_coded_contract_proved === true &&\n'
        '          evidence.checked_use === false && evidence.alpha_enrolled === false && evidence.stable_member === false;\n'
        '      }\n\n')
    if source.count(marker) != 1:
        raise support.G009Error('the inherited atlas proof-status function changed')
    source = source.replace(marker,guard+marker+'        if (localResearchProved(node)) return true;\n',1)
    marker = '      function describeStatus(node) {\n'
    if source.count(marker) != 1:
        raise support.G009Error('the inherited atlas evidence label changed')
    source = source.replace(marker,marker+'        if (localResearchProved(node)) return "Independently proved research goal; not Alpha-admitted";\n',1)
    marker = '      function statusCaveat(node) {\n'
    if source.count(marker) != 1:
        raise support.G009Error('the inherited atlas evidence caveat changed')
    source = source.replace(marker,marker+
        '        if (localResearchProved(node)) return "The complete finite signed G009 contract has original HA and compiled Lean evidence, including six ordinary empty-context certificates. These 90 new research theorems are not Alpha or Stable admissions; the existing Alpha v31 catalogue remains unchanged.";\n',1)
    snapshot = json.dumps(campaign,ensure_ascii=False,allow_nan=False,separators=(',',':'))
    if '</script' in snapshot.lower() or len(snapshot.encode()) > MAX_CAMPAIGN_BYTES:
        raise support.G009Error('unsafe or oversized embedded research campaign')
    return _expected(source,snapshot)[1].encode()


def build_files_for_verified_reader(corpus,report,state,selection):
    """In-memory display only; the fresh eight-worker caller owns publication."""
    binding = source_binding()
    root,pin = _research_evidence(corpus,report,state,selection)
    parents = parent_files()
    original = json.loads(parents['campaign.json'])
    catalog = load_catalog(ROOT/CATALOG_PATH,expected_sha256=CATALOG_SHA256)
    campaign = _project(original,catalog,corpus,root,pin,report)
    graph = build_definition_graph(campaign)
    if graph['reviewed_definition_count'] != 383 or graph['reviewed_definition_edge_count'] != 825:
        raise support.G009Error('the exact383-definition/825-edge G009 registry changed')
    audit = validate_campaign_dags(campaign,definition_graph=graph,catalog=catalog,
                                   catalog_sha256=CATALOG_SHA256)
    data = asdict(audit)
    data['research_proof_dag'] = {
        'purpose':'Separate actual checked research dependency cone; never Alpha authority',
        'theorem_count':461,'new_theorem_count':90,'inherited_alpha_theorem_count':371,
        'ordered_names_sha256':selection.plan.ordered_names_sha256,
        'dependency_edges':selection.plan.dependency_edge_count,
        'bundle_sha256':pin.sha256,'all_theorem_bodies_original_ha_checked':True,
        'same_bytes_compiled_lean_checked':True,'ordinary_principal_count':6,
        'notation_edges_are_proof_premises':False,
    }
    result = {'campaign.json':_json(campaign),'definitions.json':_json(graph),
              'dag-audit.json':_json(data),'index.html':_html(parents['index.html'].decode(),campaign,graph)}
    if parent_files() != parents or source_binding() != binding:
        raise support.G009Error('the frozen v31 atlas changed while rendering G009')
    return result


__all__ = ('build_files_for_verified_reader','source_binding')
