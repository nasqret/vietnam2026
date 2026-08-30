#!/usr/bin/env python3
"""Canonical local G009 readers, gated by this process's fresh eight workers.

The frozen non-admitting QR renderer and five original assets are reused.
Only its historical parent-count sentence and returned graph metadata are
adapted in new output. No historical module global, source or snapshot is
changed. A stored receipt is never an input, and unset final pins stop the
build before any verified page or snapshot is produced.
"""

from __future__ import annotations

import ast
import ctypes
from dataclasses import asdict, dataclass, field
import gc
from hashlib import sha256
from html import unescape
from importlib import import_module
import json
import os
from pathlib import Path, PurePosixPath
import re
import resource
import secrets
import selectors
import signal
import stat
import sys
from tempfile import TemporaryDirectory
import time
from types import FunctionType, SimpleNamespace

import constructive_g009_support as support
import build_constructive_bottom_layer_explorer as model
import build_constructive_dirichlet_explorer as old_transport
import check_constructive_g009 as proof_audit
import constructive_bottom_layer_explorer_renderer as render
import constructive_g009_checkpoints as checkpoints
from constructive_formula_compactor import _FormulaCompactor
from constructive_g009_definitions import G009_DEFINITIONS, definition_closure
from peano_lab.engine.state import proof_metrics
from peano_lab.library import campaign_bottom_layer_closure as closure
from peano_lab.library.bertrand_defined_edition import ALL_BERTRAND_DEFINITIONS
from peano_lab.library.proof_bundle import decode_proof_bundle


HERE, ROOT = Path(__file__).resolve().parent, support.ROOT
IN_REPOSITORY = HERE == ROOT/'scripts'
if not IN_REPOSITORY:
    raise RuntimeError('G009 reader must reside in its repository scripts directory')
OUTPUT = ROOT/'book/_static/constructive-g009-explorer'
TEST_FILE = ROOT/'peano-lab/py/tests/test_constructive_g009_explorer.py'
CAMPAIGN_TEST_FILE = ROOT/'peano-lab/py/tests/test_constructive_g009_campaign.py'
RFC = ROOT/'research/arithmetic-library/g009-multiplicative-convolution-rfc-v1.md'
SCHEMA = 'peano-lab-local-g009-proof-explorer-v1'
HTML_REVISION = '6c9ebfb3c37e'
SLUG, PREFIX = 'multiplicative-convolution', 'MX'
PUBLIC_PROOFS_BASE = 'https://bnaskrecki.faculty.wmi.amu.edu.pl/proofs/'
ASSET_DIGESTS = model.ASSET_DIGESTS
_digest, _json = model._digest, model._json
ExplorerError = model.BottomLayerExplorerError
RENDER_SCHEMA = 'peano-lab-g009-fresh-render-v1'
RENDER_WALL_SECONDS, RENDER_TIMEOUT_SECONDS = 180, 185
MAX_RENDER_MESSAGE_BYTES = 8192
MAX_RENDER_FILES = closure.DEFAULT_BUNDLE_LIMITS.max_nodes
EXPECTED_READER_TESTS = 277
CONTROLLER_WALL_SECONDS = proof_audit.CONTROLLER_WALL_SECONDS+RENDER_TIMEOUT_SECONDS
PRIOR_RENDER_SHA256 = '9af696515cbf99a7238e0b8e4c56b0ee17d2ad99463673a6883389b031158c67'
ATOMIC_RENAME_SOURCE = ROOT/'scripts/constructive_alpha_v31_publication_process.py'
ATOMIC_RENAME_SOURCE_SHA256 = '6cc39f32255b0e36317bd1b9b806d0aa6031e7fcd39ebcab0396df440ed3b828'
EXTRA_DEFINITIONS = ('ArithTableEqual','ArithPositiveEqual','ArithScale','SignedAdd',
                    'SignedMul','SignedPrefixSum','ArithSlice','SignedSliceSum',
                    'ArithRowSums','SignedRectangularSum','SignedZeroWindow',
                    'DirichletEntry','DirichletPrefix','DirichletSum','DirichletTable',
                    'DirichletInverse','DirichletUnitAtOne')


class RenderProcessError(ExplorerError):
    """A live-only rendering or literal-output boundary failed closed."""


def family():
    roots = checkpoints.PRINCIPAL_ROOTS
    if (type(roots) is not tuple or len(roots) != 6 or len(set(roots)) != 6
            or roots[-1] != 'dirichlet_convolution_multiplicative_exists_unique'):
        raise ExplorerError('the exact six G009 principal identities changed')
    return model.Family(SLUG,PREFIX,'Multiplicative Dirichlet convolution',
        'Actual divisor pairs · support reindexing · finite signed closure',
        'Construct a convolution table of normalized multiplicative signed prefixes and prove its complete coprime product law and positive-value uniqueness.',
        'MultiplicativePrefix(N,F) ∧ MultiplicativePrefix(N,G) ⇒ ∃H. DirichletTable(N,F,G,H) ∧ MultiplicativePrefix(N,H)',
        'D01','F01',('G009',),roots,SLUG,EXTRA_DEFINITIONS,
        'MultiplicativePrefix requires N>0 and the actual value F(1)=+1, not merely ±1. The product law covers positive coprime m,n with mn≤N. Zeroth values and table representations are unrestricted; uniqueness compares represented positive values only. Actual incidence, Cartesian tables and finite folds are constructed. This local research checkpoint performs no Alpha or Stable admission. General prime-power fields (G091) remain open.',
        'finite_signed_G009_multiplicative_convolution_closure_locally_proved_not_admitted')


def _atlas():
    module = import_module('extend_constructive_g009_campaign')
    if not callable(getattr(module,'source_binding',None)) or not callable(getattr(module,'build_files_for_verified_reader',None)):
        raise ExplorerError('the source-bound local research atlas adapter is incomplete')
    return module


def _source(path):
    return model._bounded_source(Path(path))


def _definition_input_paths():
    """Follow only literal conservative-registry imports, never run a factory."""
    found = {}
    pending = [HERE/'constructive_g009_definitions.py',HERE/'constructive_g009_definition_graph.py']
    while pending:
        path = pending.pop()
        if path in found:
            continue
        if len(found) >= 64:
            raise ExplorerError('the bounded conservative-registry source graph grew unexpectedly')
        raw = _source(path)
        found[path] = raw
        for node in ast.walk(ast.parse(raw)):
            if (isinstance(node,ast.ImportFrom) and node.module
                    and re.fullmatch(r'constructive_[a-z0-9_]+_(definitions|definition_graph|defined_adapter)',node.module)):
                base = HERE if node.module.startswith('constructive_g009_') else ROOT/'scripts'
                pending.append(base/(node.module+'.py'))
    return tuple(sorted(found,key=str))


def _render_binding():
    """Fresh byte and exact metadata fingerprint; never a proof acceptance."""
    pin = checkpoints.require_final_inventory()
    if support.PARENT_CATALOG_PINS[0].sha256[:12] != HTML_REVISION:
        raise ExplorerError('the current sealed Alpha navigation revision changed')
    records = []
    for item in support.MATH_SOURCE_PINS:
        raw = _source(support.MATH_DIRECTORY/Path(item.path).name)
        if len(raw) != item.bytes or _digest(raw) != item.sha256:
            raise ExplorerError('a frozen mathematical source changed before display')
        records.append((item.path,item.bytes,item.sha256))
    for item in support.PARENT_CONTROL_PINS:
        support.check_pin(item,ROOT,support.MAX_SOURCE_BYTES)
        records.append((item.path,item.bytes,item.sha256))
    for item in support.PARENT_CATALOG_PINS:
        support.check_pin(item,ROOT,support.MAX_CATALOG_COMPONENT_BYTES)
        records.append((item.path,item.bytes,item.sha256))
    paths = (Path(__file__),TEST_FILE,RFC,CAMPAIGN_TEST_FILE,ATOMIC_RENAME_SOURCE,
        ROOT/'conftest.py',ROOT/'pytest.ini',ROOT/'peano-lab/py/tests/conftest.py',
        *(ROOT/'peano-lab/py/tests'/name for name in (
            'test_constructive_bottom_layer_explorer.py','test_constructive_frontier_explorer.py',
            'test_constructive_historical_publication_v31.py')),
        *_definition_input_paths(),
        *(HERE/name for name in ('constructive_g009_support.py','constructive_g009_checkpoints.py',
            'check_constructive_g009.py','export_constructive_g009.py',
            'constructive_g009_definitions.py','constructive_g009_definition_graph.py',
            'extend_constructive_g009_campaign.py')),
        *(ROOT/'scripts'/name for name in ('build_constructive_bottom_layer_explorer.py',
            'constructive_bottom_layer_explorer_renderer.py','build_constructive_dirichlet_explorer.py',
            'constructive_formula_compactor.py','constructive_historical_graph_test_support.py')))
    records.extend((support._repository_path(path),len(raw),_digest(raw)) for path in paths for raw in (_source(path),))
    old = _source(ROOT/'scripts/build_constructive_dirichlet_explorer.py')
    if _digest(old) != PRIOR_RENDER_SHA256:
        raise ExplorerError('the immutable reviewed render transport changed')
    if _digest(_source(ATOMIC_RENAME_SOURCE)) != ATOMIC_RENAME_SOURCE_SHA256:
        raise ExplorerError('the immutable atomic no-replace primitive changed')
    assets = model._assets()
    checkpoints.independent._check_lean_binary()
    return _digest(support.canonical({'inputs':records,'artifact':asdict(pin),
        'new_specs_sha256':support.NEW_SPECS_SHA256,'principals':list(checkpoints.PRINCIPAL_ROOTS),
        'family':asdict(family()),'assets':[(key,_digest(value)) for key,value in sorted(assets.items())],
        'checker':[checkpoints.independent.LEAN_BINARY_BYTES,checkpoints.independent.LEAN_BINARY_SHA256],
        'atlas':_atlas().source_binding()}))


def _validate_live_report(report, state, selected):
    """Validate a live display projection, not a receipt-loading API."""
    pin = checkpoints.require_final_inventory()
    if (type(state) is not support.CandidateState or type(selected) is not support.SupportSelection
            or state.rows != selected.owned or state.sources != support.MATH_SOURCE_PINS
            or len(selected.owned) != 90 or selected.current_support
            or len(selected.complete_specs) != 461 or len(selected.parent_support) != 371
            or len({row.name for row in selected.complete_specs}) != 461
            or tuple(row.name for row in selected.complete_specs) != tuple(row.name for row in selected.plan.rows)
            or state.specs_sha256 != support.NEW_SPECS_SHA256
            or closure._specs_digest(state.rows) != state.specs_sha256
            or closure._specs_digest(selected.frontier) != selected.plan.frontier_specs_sha256):
        raise ExplorerError('the retained exact ninety-row/371-parent syntax changed')
    owned = {row.name for row in selected.owned}
    if selected.parent_support != tuple(row.name for row in selected.complete_specs if row.name not in owned):
        raise ExplorerError('retained inherited roles do not partition the actual complete cone')
    for index,(plan_row,spec) in enumerate(zip(selected.plan.rows,selected.complete_specs,strict=True)):
        if (plan_row.node_id != index or plan_row.dependencies != spec.dependencies
                or plan_row.statement_sha256 != _digest(spec.statement)):
            raise ExplorerError('a retained proof-node position, target or dependency changed')
    keys = {'schema','fresh_worker_count','stored_receipt_is_proof_authority','published',
            'alpha_admission_performed','stable_admission_performed','novelty','checkpoint',
            'principal_roots','multiplicative_convolution_principals_checked','peak_rss_bytes'}
    if (type(report) is not dict or set(report) != keys
            or report['schema'] != 'peano-g009-local-research-checkpoint-v1'
            or type(report['fresh_worker_count']) is not int or report['fresh_worker_count'] != 8
            or any(report[key] is not False for key in ('stored_receipt_is_proof_authority','published',
                                                       'alpha_admission_performed','stable_admission_performed'))
            or report['multiplicative_convolution_principals_checked'] is not True
            or type(report['peak_rss_bytes']) is not int or not 0 < report['peak_rss_bytes'] <= proof_audit.MAX_RSS_BYTES
            or proof_audit.canonical_message(report['novelty']) != proof_audit.canonical_message(proof_audit.expected_novelty(state))):
        raise ExplorerError('the complete fresh G009 audit is missing or changed')
    wanted = checkpoints.expected_report(pin,state,selected)
    if proof_audit.canonical_message(report['checkpoint']) != proof_audit.canonical_message(wanted):
        raise ExplorerError('the fresh bundle inventory differs from its exact syntax')
    roots = report['principal_roots']
    if type(roots) is not list or len(roots) != 6:
        raise ExplorerError('six actual ordinary principals are required')
    for name,row in zip(checkpoints.PRINCIPAL_ROOTS,roots,strict=True):
        expected = checkpoints.expected_root_report(pin,selected,name)['principal_roots'][0]
        if (type(row) is not dict or set(row) != set(expected)|{'ordinary_certificate_nodes'}
                or any(row[key] != value or type(row[key]) is not type(value) for key,value in expected.items())
                or type(row['ordinary_certificate_nodes']) is not int
                or not 1 < row['ordinary_certificate_nodes'] <= closure.DEFAULT_LAYERED_REPLAY_LIMITS.max_candidate_proof_occurrences):
            raise ExplorerError('an exact empty-context principal certificate is missing')
    return pin


def _local_flags():
    return {**model._local_flags(),'alpha_first_enrolled_version':None,
            'alpha_edition_version':None,'alpha_evidence':None,'first_admitted_version':None}


def _presentation_report(report):
    """Deterministic display of an already checked live report, not authority.

    The measured peak stays in the controller's actual report and stdout.
    Do not invent a repeatable observation or weaken its real resource gate.
    Only that observation is omitted from persisted reader bytes.
    """
    if (type(report) is not dict or type(report.get('peak_rss_bytes')) is not int
            or not 0 < report['peak_rss_bytes'] <= proof_audit.MAX_RSS_BYTES):
        raise ExplorerError('the real peak must satisfy its original bound before display')
    return {**{key:value for key,value in report.items() if key != 'peak_rss_bytes'},
        'schema':'peano-g009-local-research-audit-presentation-v1',
        'proof_audit_schema':report['schema'],
        'resource_policy':{'cpu_limits':list(proof_audit.CPU_LIMITS),
            'wall_seconds_per_worker':proof_audit.WALL_SECONDS,
            'max_rss_bytes':proof_audit.MAX_RSS_BYTES,
            'observed_peak_within_limit':True,'observed_peak_serialized':False}}


def _definition_records(specs):
    # Same reviewed pure formatter, resolving the new conservative closure in
    # this module only. Neither old globals nor old definition objects change.
    function = old_transport._definition_records
    local = FunctionType(function.__code__,globals(),function.__name__,function.__defaults__,function.__closure__)
    local.__kwdefaults__ = None if function.__kwdefaults__ is None else dict(function.__kwdefaults__)
    return local(specs)


def _corpus(report, state, selected, pin, bundle):
    item = family()
    tags = model._tags(item,state.rows)
    if tags[item.roots[-1]] != 'MX0059':
        raise ExplorerError('the final convolution-closure tag moved')
    definitions = definition_closure(tuple(dict.fromkeys((
        *(definition.name for definition in ALL_BERTRAND_DEFINITIONS),
        *EXTRA_DEFINITIONS,*(definition.name for definition in G009_DEFINITIONS)))))
    compactor = _FormulaCompactor(definitions)
    positions = {row.name:row.node_id for row in selected.plan.rows}
    owners = {}
    offset = 0
    for factory,pin_source in zip(support.FACTORIES,state.sources,strict=True):
        for row in state.rows[offset:offset+factory.count]:
            owners[row.name] = factory,pin_source
        offset += factory.count
    if offset != 90 or len(owners) != 90:
        raise ExplorerError('the exact nine mathematical source ownership slices changed')
    nodes = []
    for row in state.rows:
        owner,source_pin = owners[row.name]
        reading = compactor.compact(row.statement)
        model._compact_script(row,compactor,reading)
        body_nodes,body_depth = proof_metrics(bundle.nodes[positions[row.name]].body)
        source = {'source_module':'peano_lab.library.'+owner.module,'factory':owner.factory,
                  'source_sha256':source_pin.sha256,'statement_sha256':_digest(row.statement),
                  'script_sha256':_digest('\n'.join(row.script)+'\n'),'selected':True}
        nodes.append({'id':tags[row.name],'name':row.name,'summary':row.summary,
            'statement':row.statement,'statement_sha256':source['statement_sha256'],
            'script':list(row.script),'dependencies':list(row.dependencies),
            'source_module':source['source_module'],'source_filename':owner.module+'.py',
            'factory':owner.factory,'sources':[source],'inventory_role':'new_owned_theorem',
            'status':render.STATUS,**_local_flags(),'proof_bundle_node_id':positions[row.name],
            'proof_bundle_sha256':pin.sha256,'body_proof_nodes':body_nodes,'body_proof_depth':body_depth,
            'campaign_milestone':'G009','defined':reading})
    used = {identifier for node in nodes for identifier in node['defined']['definition_uses']}
    wanted_names = {item.name for item in G009_DEFINITIONS}|set(EXTRA_DEFINITIONS)
    displayed = definition_closure(tuple(item.name for item in definitions
                                        if item.stable_id in used or item.name in wanted_names))
    records = _definition_records(displayed)
    direct = {name for row in state.rows for name in row.dependencies if name not in tags}
    external = []
    for row in selected.complete_specs:
        if row.name in tags:
            continue
        if selected.role(row.name) != 'inherited_alpha_v31':
            raise ExplorerError('an inherited execution-frontier row was recounted as new')
        external.append({'name':row.name,'statement':row.statement,'statement_sha256':_digest(row.statement),
            'script':list(row.script),'script_sha256':_digest('\n'.join(row.script)+'\n'),
            'dependencies':list(row.dependencies),'proof_bundle_node_id':positions[row.name],
            'inventory_role':'inherited_alpha_v31','counted_as_new_owned_theorem':False,
            'direct_prerequisite_of_owned_theorem':row.name in direct,'parent_alpha_version':'v31',
            'alpha_checked_use':True,'enrolled_in_alpha':True,'admitted_to_alpha':True,
            'first_admission_reclassified':False,
            'reference_route':SLUG+'/checkpoint.html#theorem-'+row.name})
    routes = {row['name']:row['reference_route'] for row in external}
    if len(external) != 371 or not direct <= routes.keys():
        raise ExplorerError('the complete inherited proof support is missing')
    layers,paths,adjacency = {},{},{}
    for node in nodes:
        name = node['name']
        predecessors = [value for value in node['dependencies'] if value in tags]
        if not set(predecessors) <= layers.keys():
            raise ExplorerError('a new proof dependency is cyclic or forward')
        layers[name] = max((layers[value]+1 for value in predecessors),default=0)
        previous = max(predecessors,key=lambda value:len(paths[value]),default=None)
        paths[name] = ([] if previous is None else paths[previous])+[tags[name]]
        adjacency[name] = {'dependencies':predecessors,
            'dependents':[other['name'] for other in nodes if name in other['dependencies']],
            'critical_root_path':paths[name]}
    proof_edges = [{'kind':'proof_dependency','source':tags[name],'target':node['id']}
                   for node in nodes for name in node['dependencies'] if name in tags]
    usage_edges = [{'kind':'uses_definition','source':node['id'],'target':identifier,'occurrence_count':count,
                    'statement_occurrences':node['defined']['statement_definition_uses'].get(identifier,0),
                    'local_proposition_occurrences':node['defined']['script_definition_uses'].get(identifier,0)}
                   for node in nodes for identifier,count in node['defined']['definition_uses'].items()]
    definition_edges = [{'kind':'definition_uses_definition','source':row['id'],'target':value}
                        for row in records for value in row['dependencies']]
    return {'schema':SCHEMA,'publication_scope':'local-only-checkpoint',**_local_flags(),
        'family_slug':SLUG,'family_title':item.title,'campaign_domain_id':item.domain,
        'campaign_family_id':item.family_id,'campaign_goal_id':'G009','campaign_milestone_ids':['G009'],
        'campaign_goal_scope':item.goal_scope,'published_atlas_changed':False,
        'root_names':list(item.roots),'nodes':nodes,'definitions':records,
        'external_dependencies':external,'external_theorem_routes':routes,
        'edges':proof_edges+usage_edges+definition_edges,'node_count':90,'new_theorem_count':90,
        'edge_count':sum(len(node['dependencies']) for node in nodes),'internal_edge_count':len(proof_edges),
        'external_dependency_count':len(direct),'inherited_support_count':371,'complete_theorem_count':461,
        'definition_count':len(records),'definition_dependency_count':len(definition_edges),
        'definition_layer_count':max((row['topological_layer']+1 for row in records),default=0),
        'definition_topological_order':[row['id'] for row in records],
        'formal_line_count':sum(len(node['script']) for node in nodes),'candidate_status':render.STATUS,
        'proof_bundle_sha256':pin.sha256,'proof_bundle_node_count':pin.nodes,
        'checkpoint_report':_presentation_report(report),'local_checkpoint_verified_node_count':90,
        'alpha_enrolled_node_count':0,'alpha_checked_use_node_count':0,'stable_admitted_node_count':0,
        'parent_alpha_edition_version':'v31','parent_alpha_checked_use_count':3796,'parent_stable_count':432,
        'parent_alpha_catalog_sha256':support.PARENT_CATALOG_PINS[0].sha256,
        'navigation_revision':HTML_REVISION,'reserved_tag_slots':{},'tags':tags,'layers':layers,
        'proof_adjacency':adjacency,'proof_paths':{tags[name]:path for name,path in paths.items()},
        'path_policy':'proof_dependency_edges_only',
        'graph_scope':'new_owned_theorems_and_definitions; all inherited bodies linked in exact checkpoint'}


def _document(title, body, *, prefix):
    return (f'<!doctype html>\n<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">'
        f'<meta name="robots" content="noindex"><meta name="proof-publication-scope" content="local-only-checkpoint">'
        f'<title>{render._e(title)}</title><link rel="stylesheet" href="{render._versioned(prefix+"assets/proofs.css",HTML_REVISION)}">'
        f'</head><body class="family-page">{body}</body></html>\n').encode()


def _intended_public_metadata(path, payload):
    """Head-only delivery metadata, not a deployment or admission assertion."""
    if (type(path) is not str or not path.startswith(SLUG+'/') or not path.endswith('.html')
            or re.fullmatch(re.escape(SLUG)+r'/[A-Za-z0-9_/-]+\.html',path) is None
            or any(part in ('','.','..') for part in path.split('/')) or '\\' in path
            or type(payload) is not bytes or payload.count(b'</head>') != 1):
        raise ExplorerError('public family metadata needs one exact safe HTML head')
    head,tail = payload.split(b'</head>',1)
    if (re.search(rb'\brel\s*=\s*[\"\']canonical[\"\']',head,re.I)
            or re.search(rb'\bproperty\s*=\s*[\"\']og:url[\"\']',head,re.I)):
        raise ExplorerError('an inherited canonical identity cannot be silently replaced')
    route = path.removesuffix('index.html') if path.endswith('/index.html') else path
    url = render._e(PUBLIC_PROOFS_BASE+route)
    additions = f'<link rel="canonical" href="{url}">\n<meta property="og:url" content="{url}">\n'
    if not re.search(rb'\bproperty\s*=\s*[\"\']og:type[\"\']',head,re.I):
        additions += '<meta property="og:type" content="website">\n'
    if not re.search(rb'\bproperty\s*=\s*[\"\']og:title[\"\']',head,re.I):
        title = re.search(rb'<title>(.*?)</title>',head,re.S|re.I)
        if title is None:
            raise ExplorerError('the canonical family page has no exact title')
        additions += '<meta property="og:title" content="'+render._e(unescape(title.group(1).decode()))+'">\n'
    return head+additions.encode()+b'</head>'+tail


def _checkpoint_page(corpus, report):
    articles = []
    for row in (*corpus['nodes'],*corpus['external_dependencies']):
        own = row['name'] in corpus['tags']
        link = (f'<a href="{render._versioned("explorer/defined/tag/"+corpus["tags"][row["name"]]+".html",HTML_REVISION)}">Read theorem</a>' if own else 'Inherited current Alpha v31 premise; first admission unchanged')
        inherited_script = ('' if own else '<details><summary>Exact inherited tactic source</summary><pre><code>'
                            +render._e('\n'.join(row['script']))+'</code></pre></details>')
        articles.append(f'<article class="view-card" id="theorem-{render._e(row["name"])}"><h3>{render._e(row["name"])}</h3><p>{link}</p>'
            f'<p>Actual complete-bundle node {row["proof_bundle_node_id"]}; statement SHA-256 <code>{row["statement_sha256"]}</code>.</p>'
            f'<details><summary>Exact first-order statement</summary><pre>{render._e(row["statement"])}</pre></details>{inherited_script}</article>')
    pin = checkpoints.FINAL_ARTIFACT
    roots = ''.join(f'<li>{render._e(row["name"])}: {row["ordinary_certificate_nodes"]} actual empty-context HA certificate nodes</li>' for row in report['principal_roots'])
    source_links = ''.join(f'<li><a href="{render._versioned("../sources/"+Path(row.path).name,HTML_REVISION)}">{render._e(row.path)}</a> · <code>{row.sha256}</code></li>' for row in support.MATH_SOURCE_PINS)
    body = f'<header class="family-hero"><div class="shell"><nav class="crumbs"><a href="{render._versioned("./",HTML_REVISION)}">Proof family</a><span>/</span><a href="{render._versioned("../grand-campaign/?view=goal&focus=G009",HTML_REVISION)}">Research campaign</a></nav><h1>Exact G009 research checkpoint</h1><p class="lede">{render._e(render.STATUS)}</p></div></header>'
    body += f'<main class="shell family-main"><section class="release-note"><strong>Complete mathematical inventory:</strong> 90 genuinely new theorems and 371 inherited Alpha-v31 theorems; {pin.nodes} bundle nodes including packaging. All bodies passed original HA and the independent compiled Lean verifier in this fresh run. The six listed principals additionally passed ordinary empty-context HA replay. Support is never recounted as new. Alpha remains 3796; Stable remains 432.</section>'
    body += f'<section class="release-note"><a href="{render._versioned("../checkpoints/"+Path(pin.path).name,HTML_REVISION)}">Literal checked proof bundle</a> · {pin.bytes} bytes · SHA-256 <code>{pin.sha256}</code> · <a href="{render._versioned("api/checkpoint.json",HTML_REVISION)}">Fresh audit report</a></section><section><h2>Ordinary principal certificates</h2><ul>{roots}</ul><h2>Exact authoring sources</h2><ul>{source_links}</ul><a href="{render._versioned("../sources/"+RFC.name,HTML_REVISION)}">Campaign RFC</a></section><section><h2>Every owned theorem and inherited proof body</h2>{"".join(articles)}</section></main>'
    return _document('Exact local G009 checkpoint',body,prefix='../')


def _index(corpus):
    root = corpus['tags'][family().roots[-1]]
    body = f'<header class="family-hero"><div class="shell"><nav class="crumbs"><a href="{render._versioned("grand-campaign/",HTML_REVISION)}">Research atlas</a></nav><p class="eyebrow">Constructive arithmetic · local research</p><h1>Multiplicative Dirichlet convolution</h1><p class="lede">Ninety new, freshly checked research theorems over the unchanged Alpha-v31 library.</p></div></header><main class="shell family-main"><section class="view-grid"><article class="view-card featured"><h2>Canonical proof family</h2><p>Actual support-only reindexing, divisor-pair decomposition, Cartesian sums and normalized finite convolution closure.</p><a href="{render._versioned(SLUG+"/",HTML_REVISION)}">Enter the exact and defined readers →</a></article><article class="view-card"><h2>Final theorem</h2><a href="{render._versioned(SLUG+"/explorer/defined/tag/"+root+".html",HTML_REVISION)}">{root}: constructed multiplicative convolution</a></article><article class="view-card"><h2>Campaign context</h2><a href="{render._versioned("grand-campaign/?view=goal&focus=G009",HTML_REVISION)}">Inspect the local research closure of G009 →</a></article></section><section class="release-note">Generating this research checkpoint performs no Alpha or Stable admission and no remote deployment. Alpha v31 remains 3796; Stable remains 432. General G091 remains open. <a href="{render._versioned("checkpoints.json",HTML_REVISION)}">Exact inventory and evidence boundaries</a>.</section></main>'
    return _document('Local G009 proof checkpoint',body,prefix='')


def _render_files(report, syntax, binding):
    if (type(syntax) is not tuple or len(syntax) != 3 or type(syntax[2]) is not bytes
            or syntax[2] != proof_audit.canonical_message(report)):
        raise ExplorerError('rendering needs this live audit callback, not saved report input')
    state,selected,_ = syntax
    pin = _validate_live_report(report,state,selected)
    if _render_binding() != binding:
        raise ExplorerError('sources changed between actual proof checks and rendering')
    payload = closure._read_pinned(ROOT/pin.path,pin.bytes,pin.sha256)
    bundle,target = decode_proof_bundle(payload.decode('utf-8'))
    if len(bundle.nodes) != pin.nodes or pin.nodes != len(selected.complete_specs)+1:
        raise ExplorerError('the actual complete proof bundle has a different inventory')
    corpus = _corpus(report,state,selected,pin,bundle)
    # Only literal proof bytes and extracted display metrics are needed from
    # here. Discard unused decoded certificate syntax before the atlas loads
    # the full current catalogue; no checker, cache or proof limit changes.
    del bundle,target
    gc.collect()
    item = family()
    graph = render.graph_payload(item,corpus,revision=HTML_REVISION)
    graph['parent_alpha_edition_version'] = 'v31'
    graph['parent_alpha_checked_use_count'] = 3796
    graph['inherited_support_count'] = 371
    graph['graph_scope'] = corpus['graph_scope']
    files = model._assets()
    base = SLUG+'/'
    landing = render.render_local_family_landing(item,corpus,revision=HTML_REVISION,bundle_node_count=pin.nodes)
    old_sentence = b'Alpha v30 remains 3222 theorems and Stable remains 432.'
    if landing.count(old_sentence) != 1:
        raise ExplorerError('the exact canonical parent-count sentence changed')
    files[base+'index.html'] = landing.replace(old_sentence,b'Alpha v31 remains 3796 theorems and Stable remains 432.',1)
    files[base+'checkpoint.html'] = _checkpoint_page(corpus,report)
    files[base+'api/corpus.json'] = _json(corpus)
    files[base+'api/checkpoint.json'] = proof_audit.canonical_message(_presentation_report(report))
    files[base+'api/graph.json'] = files[base+'explorer/defined/api/graph.json'] = _json(graph)
    files[base+'explorer/index.html'] = render.render_exact_index(item,corpus,corpus['tags'],corpus['layers'],
        stylesheet_href='../../assets/exact-explorer.css?v='+ASSET_DIGESTS['exact-explorer.css'][:12],
        script_href='../../assets/exact-explorer.js?v='+ASSET_DIGESTS['exact-explorer.js'][:12],html_revision=HTML_REVISION)
    files[base+'explorer/defined/index.html'] = render.render_defined_index(item,corpus,revision=HTML_REVISION)
    files[base+'explorer/defined/graph.html'] = render.render_defined_graph(item,corpus,graph,revision=HTML_REVISION)
    for node in corpus['nodes']:
        tag = corpus['tags'][node['name']]
        files[base+f'explorer/tag/{tag}.html'] = render.render_exact_theorem(item,corpus,node,corpus['tags'],corpus['layers'],
            stylesheet_href='../../../assets/exact-explorer.css?v='+ASSET_DIGESTS['exact-explorer.css'][:12],
            script_href='../../../assets/exact-explorer.js?v='+ASSET_DIGESTS['exact-explorer.js'][:12],html_revision=HTML_REVISION)
        files[base+f'explorer/defined/tag/{tag}.html'] = render.render_defined_theorem(item,corpus,node,revision=HTML_REVISION)
    for definition in corpus['definitions']:
        files[base+f'explorer/defined/definition/{definition["id"]}.html'] = render.render_defined_definition(item,corpus,definition,revision=HTML_REVISION)
    files['checkpoints/'+Path(pin.path).name] = payload
    for source in state.sources:
        files['sources/'+Path(source.path).name] = _source(support.MATH_DIRECTORY/Path(source.path).name)
    files['sources/'+RFC.name] = _source(RFC)
    atlas_files = _atlas().build_files_for_verified_reader(corpus,report,state,selected)
    if (type(atlas_files) is not dict
            or set(atlas_files) != {'campaign.json','definitions.json','dag-audit.json','index.html'}
            or any(type(value) is not bytes for value in atlas_files.values())):
        raise ExplorerError('the local research atlas returned an unexpected file scope')
    files.update({'grand-campaign/'+name:payload for name,payload in atlas_files.items()})
    inventory = {'schema':SCHEMA,'publication_scope':'local-only-checkpoint','published':False,
        'alpha_admission_performed':False,'stable_admission_performed':False,'new_theorems':90,
        'inherited_alpha_v31_theorems':371,'complete_theorems':461,'inherited_support_counted_as_new':False,
        'navigation_revision':HTML_REVISION,'render_source_binding_sha256':binding,
        'multiplicative_convolution_principals_checked':True,'general_G091_prime_power_fields_proved':False,
        'parent':{'alpha_version':'v31','alpha_checked_use_count':3796,'stable_count':432,
                  'catalog_sha256':support.PARENT_CATALOG_PINS[0].sha256},
        'checkpoint':_presentation_report(report),'family_slug':SLUG,'tags':corpus['tags']}
    inventory['checkpoint_digest'] = _digest(_json(inventory))
    files['checkpoints.json'] = _json(inventory)
    files['proof-audit.json'] = proof_audit.canonical_message(_presentation_report(report))
    files['index.html'] = _index(corpus)
    for name in tuple(files):
        if name.startswith(base) and name.endswith('.html'):
            files[name] = _intended_public_metadata(name,files[name])
    files['manifest.json'] = _json({'schema':SCHEMA+'-manifest','publication_scope':'local-only-checkpoint',
        'checkpoint_digest':inventory['checkpoint_digest'],'navigation_revision':HTML_REVISION,
        'file_count_excluding_manifest':len(files),
        'files':{name:{'bytes':len(payload),'sha256':_digest(payload)} for name,payload in sorted(files.items())}})
    if _render_binding() != binding:
        raise ExplorerError('sources changed while formatting the new reader')
    return files


@dataclass(frozen=True,slots=True,eq=False)
class _FreshSnapshotTests:
    files: dict[str,bytes]
    binding: str
    state: support.CandidateState
    selected: support.SupportSelection
    report: dict
    collected: list[str] = field(default_factory=list)
    outcomes: list[tuple[str,str,bool]] = field(default_factory=list)
    rejected: list[str] = field(default_factory=list)

    def pytest_configure(self,config):
        config._g009_fresh_snapshot = self

    def pytest_deselected(self,items):
        if items:
            self.rejected.append('deselected')

    def pytest_collection_finish(self,session):
        names = tuple(item.nodeid for item in session.items)
        paths = tuple(Path(item.path).resolve() for item in session.items)
        _validate_test_collection(names,paths,collect_only=session.config.option.collectonly,
                                  rejected=tuple(self.rejected))
        self.collected.extend(names)

    def pytest_runtest_logreport(self,report):
        xfail = hasattr(report,'wasxfail')
        if report.when == 'call':
            self.outcomes.append((report.nodeid,report.outcome,xfail))
        if report.failed or report.skipped or xfail:
            self.rejected.append('failed, skipped or xfail test phase')


def _validate_test_collection(names,paths,*,collect_only,rejected):
    """Mandatory test-scheduler metadata, never a mathematical proof gate."""
    if (type(names) is not tuple or len(names) != EXPECTED_READER_TESTS
            or any(type(name) is not str or not name for name in names)
            or len(set(names)) != EXPECTED_READER_TESTS
            or type(paths) is not tuple or len(paths) != EXPECTED_READER_TESTS
            or any(path != TEST_FILE.resolve() for path in paths)
            or collect_only is not False or type(rejected) is not tuple or rejected):
        raise RenderProcessError('mandatory reader suite was filtered, collected only, skipped or changed')


def _validate_test_completion(status,collected,outcomes,rejected):
    """Every exact collected test must have an actual passing call outcome."""
    if (type(status) is not int or status != 0 or type(collected) is not tuple
            or len(collected) != EXPECTED_READER_TESTS
            or any(type(name) is not str or not name for name in collected)
            or len(set(collected)) != EXPECTED_READER_TESTS
            or type(outcomes) is not tuple or len(outcomes) != EXPECTED_READER_TESTS
            or any(type(row) is not tuple or len(row) != 3 or type(row[0]) is not str
                   or type(row[1]) is not str or row[1] != 'passed' or row[2] is not False
                   for row in outcomes)
            or tuple(row[0] for row in outcomes) != collected
            or type(rejected) is not tuple or rejected):
        raise RenderProcessError('mandatory reader tests did not all execute and pass without skips or xfail')


def _assert_snapshot_binding(files):
    value = json.loads(files['checkpoints.json'])['render_source_binding_sha256']
    if _render_binding() != value:
        raise ExplorerError('the live snapshot source binding changed')
    return value


def _run_snapshot_tests(files, immutable_before):
    import pytest
    if (type(immutable_before) is not tuple or len(immutable_before) != 3
            or type(immutable_before[0]) is not support.CandidateState
            or type(immutable_before[1]) is not support.SupportSelection
            or type(immutable_before[2]) is not dict):
        raise ExplorerError('same-live reader tests require the actual retained proof syntax')
    plugin = _FreshSnapshotTests(files,_assert_snapshot_binding(files),*immutable_before)
    status = int(pytest.main(['-q',str(TEST_FILE)],plugins=[plugin]))
    _validate_test_completion(status,tuple(plugin.collected),tuple(plugin.outcomes),tuple(plugin.rejected))
    return status


# Only reviewed transport code is rebound to THIS new module. Historical
# globals, functions, caches and assets retain their identities and bytes.
audit = SimpleNamespace(CPU_LIMITS=proof_audit.CPU_LIMITS,MAX_RSS_BYTES=proof_audit.MAX_RSS_BYTES,
    _canonical=proof_audit.canonical_message,_decode_message=proof_audit.transport._decode_message,
    canonical_report=lambda report:proof_audit.canonical_message(_presentation_report(report)).decode('utf-8'))
_RenderResult = old_transport._RenderResult


def _reuse(function):
    copied = FunctionType(function.__code__,globals(),function.__name__,function.__defaults__,function.__closure__)
    copied.__kwdefaults__ = None if function.__kwdefaults__ is None else dict(function.__kwdefaults__)
    copied.__annotations__ = dict(function.__annotations__)
    return copied


_validate_render_message = _reuse(old_transport._validate_render_message)
_read_rendered_files = _reuse(old_transport._read_rendered_files)
_render_child = _reuse(old_transport._render_child)
_reviewed_fork_render_phase = _reuse(old_transport._fork_render_phase)


def _fork_render_phase(*args,**kwargs):
    started = time.monotonic()
    result = _reviewed_fork_render_phase(*args,**kwargs)
    if time.monotonic()-started >= RENDER_WALL_SECONDS:
        raise RenderProcessError('the complete render/validation phase exceeded its original wall window')
    return result


def _atomic_renamer():
    """Use only the byte-pinned, unchanged native no-replace primitive.

    Loading this one reviewed function avoids importing the historical
    publisher's whole model or changing any of its module globals.
    """
    raw = _source(ATOMIC_RENAME_SOURCE)
    if _digest(raw) != ATOMIC_RENAME_SOURCE_SHA256:
        raise RenderProcessError('the exact reviewed atomic rename source changed')
    functions = [node for node in ast.parse(raw).body
                 if isinstance(node,ast.FunctionDef) and node.name == '_rename_new']
    if len(functions) != 1 or functions[0].decorator_list:
        raise RenderProcessError('the exact atomic rename primitive is missing')
    namespace = {'ctypes':ctypes,'os':os,'sys':sys,'Path':Path,
                 'PublicationProcessError':RenderProcessError}
    exec(compile(ast.Module(body=functions,type_ignores=[]),str(ATOMIC_RENAME_SOURCE),'exec'),namespace)
    return namespace['_rename_new']


def _directory_identity(path):
    value = Path(path).lstat()
    if not stat.S_ISDIR(value.st_mode) or value.st_uid != os.geteuid():
        raise RenderProcessError('the generated directory is not regular and owned')
    return value.st_dev,value.st_ino


def _preflight_output(output, *, check):
    """No proof jobs or writes for an existing creation target or unsafe path."""
    if type(check) is not bool or not isinstance(output,(str,Path)):
        raise RenderProcessError('output mode and path must be explicit')
    destination = Path(output)
    if not destination.is_absolute() or '..' in destination.parts:
        raise RenderProcessError('the output must be an explicit absolute bounded target')
    for parent in (*reversed(destination.parent.parents),destination.parent):
        value = parent.lstat()
        if not stat.S_ISDIR(value.st_mode):
            raise RenderProcessError('the output has a symlink or non-directory ancestor')
    if check:
        _directory_identity(destination)
    else:
        try:
            destination.lstat()
        except FileNotFoundError:
            pass
        else:
            raise RenderProcessError('refusing to overwrite an existing reader tree')
    return destination


def _commit_tree(source, destination, files, *, check, final_check):
    """Private byte-tree transaction only, never a proof acceptance API."""
    if (type(files) is not dict or not 0 < len(files) <= MAX_RENDER_FILES
            or any(type(value) is not bytes or len(value) > closure.DEFAULT_BUNDLE_LIMITS.max_payload_bytes
                   for value in files.values())
            or sum(map(len,files.values())) > proof_audit.MAX_RSS_BYTES or not callable(final_check)):
        raise RenderProcessError('the exact byte-tree transaction input is unbounded')
    source = _preflight_output(source,check=True)
    identity = _directory_identity(source)
    destination = _preflight_output(destination,check=check)
    model.write_or_check(files,output=source,check=True)
    final_check()
    if check:
        model.write_or_check(files,output=destination,check=True)
        final_check()
        return
    rename = _atomic_renamer()
    _preflight_output(destination,check=False)
    moved = False
    try:
        rename(source,destination)
        moved = True
        if _directory_identity(destination) != identity:
            raise RenderProcessError('the newly installed reader directory changed identity')
        model.write_or_check(files,output=destination,check=True)
        final_check()
    except BaseException:
        if moved:
            if _directory_identity(destination) != identity:
                raise RenderProcessError('rollback refused a changed or foreign directory')
            # Recover only our exact directory; never delete a competing path.
            rename(destination,source)
        raise


def _build_verified(*, output, check=False, return_snapshot=False):
    if type(return_snapshot) is not bool:
        raise ExplorerError('the private snapshot return mode must be an exact Boolean')
    destination = _preflight_output(output,check=check)
    binding, retained = _render_binding(),[]
    def collect(state,selected,payload):
        if retained or type(payload) is not bytes:
            raise ExplorerError('duplicate or mutable fresh audit projection')
        retained.append((state,selected,payload))
    report = proof_audit.verify_in_fresh_windows(syntax_collector=collect)
    if len(retained) != 1 or retained[0][2] != proof_audit.canonical_message(report):
        raise ExplorerError('the actual complete audit did not deliver its own immutable syntax projection')
    _validate_live_report(report,*retained[0][:2])
    if _render_binding() != binding:
        raise ExplorerError('proof or display sources changed across the fresh audit')
    def final_check():
        if _render_binding() != binding:
            raise RenderProcessError('sources changed before or after exclusive reader installation')
        checkpoints.peak_rss_bytes()
    with TemporaryDirectory(prefix='.g009-render-',dir=destination.parent) as directory:
        staged = Path(directory).resolve()/'files'
        result = _fork_render_phase(report,retained[0],binding,output=staged,check=False,test=True,
                                    write_audit=False,immutable_before=(*retained[0][:2],report))
        final_check()
        _commit_tree(staged,destination,result.files,check=check,final_check=final_check)
    if return_snapshot:
        final_check()
        return result.files,report['peak_rss_bytes'],result.peak_rss_bytes,retained[0]
    return result.files,report['peak_rss_bytes'],result.peak_rss_bytes


def fresh_test_snapshot():
    """Bootstrap ordinary pytest through the real eight-job/277-test build.

    The retained syntax and immutable report bytes are returned only by the
    completed build. No file, receipt, caller-supplied report or proof flag
    can supply this fixture; the nested suite receives its own real plugin.
    """
    with TemporaryDirectory(prefix='.g009-test-snapshot-',dir=OUTPUT.parent) as directory:
        files,worker_peak,render_peak,retained = _build_verified(
            output=Path(directory).resolve()/'files',return_snapshot=True)
        if (type(retained) is not tuple or len(retained) != 3
                or type(retained[0]) is not support.CandidateState
                or type(retained[1]) is not support.SupportSelection
                or type(retained[2]) is not bytes):
            raise ExplorerError('the completed fresh build did not return its actual syntax projection')
        state,selected,payload = retained
        report = proof_audit.transport._decode_message(payload)
        if type(report) is not dict or proof_audit.canonical_message(report) != payload:
            raise ExplorerError('the completed fresh report bytes are not exact and canonical')
        if (type(files) is not dict
                or any(type(name) is not str or type(value) is not bytes for name,value in files.items())
                or type(worker_peak) is not int or worker_peak != report['peak_rss_bytes']
                or type(render_peak) is not int or not 0 < render_peak <= proof_audit.MAX_RSS_BYTES):
            raise ExplorerError('the completed fresh build returned changed files or resource observations')
        files = dict(files)
        presented = proof_audit.canonical_message(_presentation_report(report))
        if any(files.get(path) != presented for path in ('proof-audit.json',SLUG+'/api/checkpoint.json')):
            raise ExplorerError('the returned byte tree differs from its actual fresh report')
        _validate_live_report(report,state,selected)
        binding = _assert_snapshot_binding(files)
        checkpoints.peak_rss_bytes()
        return _FreshSnapshotTests(files,binding,state,selected,report)


def build_files():
    """Always run eight real proof jobs and mandatory same-live reader tests."""
    with TemporaryDirectory(prefix='.g009-memory-',dir=OUTPUT.parent) as directory:
        return _build_verified(output=Path(directory).resolve()/'files')[0]


def main(argv=None):
    import argparse
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--check',action='store_true',help='fresh proofs and exact snapshot comparison')
    parser.add_argument('--test',action='store_true',help='compatibility flag: same-live tests are always mandatory')
    args = parser.parse_args(argv)
    resource.setrlimit(resource.RLIMIT_CPU,proof_audit.CPU_LIMITS)
    signal.alarm(CONTROLLER_WALL_SECONDS)
    started = time.monotonic()
    files,worker_peak,render_peak = _build_verified(output=OUTPUT,check=args.check)
    print(f'{"Checked" if args.check else "Generated"} {len(files)} canonical local G009 files; 90 new theorems, 371 inherited Alpha-v31 proofs.')
    print(f'Elapsed {time.monotonic()-started:.3f}s; worker peak {worker_peak}; render peak {render_peak}; controller peak {checkpoints.peak_rss_bytes()} bytes.')
    print('Alpha remains 3796; Stable remains 432. No admission or publication performed.')
    return 0


if __name__ == '__main__':
    sys.modules.setdefault('build_constructive_g009_explorer',sys.modules[__name__])
    raise SystemExit(main())
