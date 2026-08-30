"""Polynomial-division prerequisite reader contracts, including non-authority callback transport tests.

The protocol fixtures below contain no checked proof and never produce a
successful audit, page, bundle or publication. Actual positive reader tests
must receive this build's live eight-worker evidence, not a saved receipt.
"""

from __future__ import annotations

import ast
from copy import deepcopy
from dataclasses import dataclass, replace
from hashlib import sha256
from html.parser import HTMLParser
from importlib import import_module
import inspect
import json
from pathlib import Path
import posixpath
import re
import subprocess
import sys
from types import SimpleNamespace
from urllib.parse import parse_qs, unquote, urlsplit

import pytest

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
if HERE != ROOT/'peano-lab/py/tests' or not (ROOT/'peano-lab/py/peano_lab').is_dir():
    raise RuntimeError('Polynomial-division prerequisite reader tests must reside in their repository tests directory')
sys.path[:0] = [str(HERE),str(ROOT/'scripts'),str(ROOT/'peano-lab/py')]

import check_constructive_polynomial_division as audit
import build_constructive_polynomial_division_explorer as reader
import constructive_historical_graph_test_support as graph_observer
from constructive_polynomial_division_definitions import ALL_CONSTRUCTIVE_DEFINITIONS_BY_NAME as DEFINITIONS
from constructive_formula_compactor import _LocalDefinedParser
from peano_lab.kernel.formulas import parse_formula_with_names

assert graph_observer.ROOT == ROOT
assert Path(inspect.getfile(graph_observer.observe_graph)).resolve() == ROOT/'scripts/constructive_historical_graph_test_support.py'


def _borrow_exact_dom_contracts():
    """Use real historical JS tests without their old proof-loading fixtures.

    This selects only unchanged functions/classes from the pinned source.
    No production function, theorem source, browser asset or old test changes.
    """
    names = {
        'Document','_strict_json','_graph_runtime','_landing_structure',
        'test_every_theorem_statement_script_and_all_local_propositions_are_exact',
        'test_definition_identity_exactness_and_acyclic_three_kind_dag',
        'test_actual_canonical_dashboard_and_local_addon_combine_all_three_filters',
        'test_actual_defined_reader_highlights_initial_fragment_and_focuses_hash_changes',
        'test_actual_graph_detail_overlay_never_calls_a_local_theorem_alpha_checked',
    }
    source = reader._source(ROOT/'peano-lab/py/tests/test_constructive_bottom_layer_explorer.py')
    selected = [node for node in ast.parse(source).body
                if isinstance(node,(ast.FunctionDef,ast.ClassDef)) and node.name in names]
    assert {node.name for node in selected} == names
    for node in selected:
        node.decorator_list = []
    namespace = {'ROOT':ROOT,'builder':reader.model,'render':reader.render,
        'HTMLParser':HTMLParser,'json':json,'ast':ast,'Path':Path,'subprocess':subprocess,
        'SimpleNamespace':SimpleNamespace,'sha256':sha256,'DEFINITIONS':DEFINITIONS,
        'parse_formula_with_names':parse_formula_with_names,'_LocalDefinedParser':_LocalDefinedParser}
    exec(compile(ast.Module(body=selected,type_ignores=[]),'<unchanged canonical DOM contracts>','exec'),namespace)
    return namespace


DOM = _borrow_exact_dom_contracts()
Document, strict_json = DOM['Document'],DOM['_strict_json']


def _atlas_test_module():
    return import_module('tests.test_constructive_polynomial_division_campaign')


def _atlas_mutations():
    source = ast.parse(reader._source(reader.CAMPAIGN_TEST_FILE))
    assignment = next(node for node in source.body if isinstance(node,ast.Assign)
        and any(isinstance(target,ast.Name) and target.id == 'ACTUAL_EVIDENCE_MUTATIONS' for target in node.targets))
    result = ast.literal_eval(assignment.value)
    assert type(result) is tuple and len(result) == len(set(result)) == 44
    return result


@pytest.fixture(scope='module')
def live(pytestconfig):
    """Only this builder's real eight-job run can supply positive UI input."""
    plugin = getattr(pytestconfig,'_polynomial_division_fresh_snapshot',None)
    if plugin is None:
        plugin = reader.fresh_test_snapshot()
    assert type(plugin) is reader._FreshSnapshotTests, 'run the actual fresh builder with --test; saved receipts are not fixtures'
    assert reader._assert_snapshot_binding(plugin.files) == plugin.binding
    reader._validate_live_report(plugin.report,plugin.state,plugin.selected)
    return plugin


@pytest.fixture(scope='module')
def corpus(live):
    return strict_json(live.files[reader.SLUG+'/api/corpus.json'])


@pytest.fixture(scope='module')
def documents(live):
    return {name:Document(payload) for name,payload in live.files.items() if name.endswith('.html')}


@pytest.fixture(scope='module')
def authored_rows(pytestconfig):
    """Source-contract parsing only; no acceptance report or output exists."""
    plugin = getattr(pytestconfig,'_polynomial_division_fresh_snapshot',None)
    if plugin is not None:
        assert type(plugin) is reader._FreshSnapshotTests
        return plugin.state.rows
    return reader.support.load_candidate_state(final=False).rows


@dataclass(frozen=True)
class _TransportOnlySyntax:
    """Immutable transport sentinel; explicitly not mathematical evidence."""

    label: str = 'non-authority callback transport only'


def _failing_scheduler(monkeypatch, *, failure_at=None, changed_binding=False,
                       incomplete_roots=False):
    """Always-failing scheduling fixture, with no proof-acceptance mock.

    Earlier transport messages are deliberately not valid proof reports.
    A chosen worker, final binding, or principal-inventory gate must fail;
    callers cannot use this fixture to obtain a successful audit.
    """
    assert failure_at is not None or changed_binding or incomplete_roots
    events = []
    state = SimpleNamespace(rows=(), specs_sha256='transport-only-not-a-proof')
    selected = _TransportOnlySyntax()
    bindings = iter(('a'*64, 'b'*64 if changed_binding else 'a'*64))
    monkeypatch.setattr(audit, 'binding', lambda: next(bindings))
    monkeypatch.setattr(audit.checkpoints, 'require_final_inventory', lambda: None)
    monkeypatch.setattr(audit.support, 'load_candidate_state', lambda **_: state)
    monkeypatch.setattr(audit.support, 'select_support', lambda *_: selected)
    monkeypatch.setattr(audit.checkpoints, 'expected_report', lambda *_: {'transport_only': True})
    monkeypatch.setattr(audit.checkpoints, 'expected_root_report', lambda *_: {'transport_only': True})

    def fail_closed_worker(kind, root, source_binding, expected):
        index = len(events)
        events.append((kind, root))
        if index == failure_at:
            raise audit.support.PolynomialDivisionError('intentional transport-only worker failure')
        roots = [] if root is None or incomplete_roots else [{'name': root, 'transport_only': True}]
        return {'transport_only': True, 'principal_roots': roots}, 1

    monkeypatch.setattr(audit, 'run_worker', fail_closed_worker)
    return events


@pytest.mark.parametrize('invalid', (False, True, 0, 'collector', ()))
def test_invalid_callback_fails_before_any_inventory_or_proof_job(monkeypatch, invalid):
    def forbidden():
        raise AssertionError('invalid callback reached the proof input path')
    monkeypatch.setattr(audit, 'binding', forbidden)
    with pytest.raises(audit.support.PolynomialDivisionError, match='syntax_collector'):
        audit.verify_in_fresh_windows(syntax_collector=invalid)


@pytest.mark.parametrize('position', range(8))
def test_callback_never_receives_a_failed_worker_chain(monkeypatch, position):
    events = _failing_scheduler(monkeypatch, failure_at=position)
    delivered = []
    with pytest.raises(audit.support.PolynomialDivisionError, match='intentional transport-only'):
        audit.verify_in_fresh_windows(syntax_collector=lambda *args: delivered.append(args))
    assert len(events) == position+1 and delivered == []


def test_callback_never_receives_a_changed_final_source_binding(monkeypatch):
    events = _failing_scheduler(monkeypatch, changed_binding=True)
    delivered = []
    with pytest.raises(audit.support.PolynomialDivisionError, match='sources changed'):
        audit.verify_in_fresh_windows(syntax_collector=lambda *args: delivered.append(args))
    assert len(events) == 8 and delivered == []


def test_callback_never_receives_an_incomplete_principal_inventory(monkeypatch):
    events = _failing_scheduler(monkeypatch, incomplete_roots=True)
    delivered = []
    with pytest.raises(audit.support.PolynomialDivisionError, match='principal inventory is incomplete'):
        audit.verify_in_fresh_windows(syntax_collector=lambda *args: delivered.append(args))
    assert len(events) == 8 and delivered == []


def test_one_way_callback_payload_is_immutable_and_return_value_is_ignored(monkeypatch):
    """Test the non-verifying transport helper, never the proof controller."""
    state, selected = _TransportOnlySyntax('source'), _TransportOnlySyntax('selection')
    raw = audit.canonical_message({'transport_only': True})
    binding_events = []
    monkeypatch.setattr(audit, 'binding', lambda: binding_events.append('after-callback') or 'a'*64)
    seen = []

    def collect(actual_state, actual_selection, payload):
        assert actual_state is state and actual_selection is selected and payload is raw
        with pytest.raises(TypeError):
            payload[0] = 0
        seen.append(payload)
        return {'forged_return_is_not_authority': True}

    assert audit._collect_verified_syntax(collect, state, selected, raw, 'a'*64) is None
    assert seen == [raw] and binding_events == ['after-callback']


def test_callback_exception_propagates_without_a_report_or_output(monkeypatch, tmp_path):
    def forbidden_binding():
        raise AssertionError('an exception was swallowed')
    monkeypatch.setattr(audit, 'binding', forbidden_binding)
    def fail(*_):
        raise RuntimeError('display consumer failed')
    with pytest.raises(RuntimeError, match='display consumer failed'):
        audit._collect_verified_syntax(fail, _TransportOnlySyntax(), _TransportOnlySyntax(), b'{}\n', 'a'*64)
    assert tuple(tmp_path.iterdir()) == ()


def test_callback_source_change_fails_closed(monkeypatch):
    monkeypatch.setattr(audit, 'binding', lambda: 'b'*64)
    with pytest.raises(audit.support.PolynomialDivisionError, match='display syntax callback'):
        audit._collect_verified_syntax(lambda *_: None, _TransportOnlySyntax(),
                                       _TransportOnlySyntax(), b'{}\n', 'a'*64)


@pytest.mark.parametrize('payload', ({}, '{}', bytearray(b'{}\n')))
def test_callback_transport_rejects_mutable_or_nonbyte_reports(payload):
    with pytest.raises(audit.support.PolynomialDivisionError, match='one-way syntax callback'):
        audit._collect_verified_syntax(lambda *_: pytest.fail('callback ran'),
                                       _TransportOnlySyntax(), _TransportOnlySyntax(), payload, 'a'*64)


def test_callback_is_after_all_actual_workers_final_binding_and_aggregation():
    source = inspect.getsource(audit.verify_in_fresh_windows)
    tree = ast.parse(source)
    calls = [node for node in ast.walk(tree) if isinstance(node, ast.Call)]
    callback = next(node for node in calls if isinstance(node.func, ast.Name)
                    and node.func.id == '_collect_verified_syntax')
    workers = [node for node in calls if isinstance(node.func, ast.Name) and node.func.id == 'run_worker']
    assert len(workers) == 3 and max(node.lineno for node in workers) < callback.lineno
    assert source.index('if binding() != source_binding:') < source.index('result = {')
    assert source.index('if tuple(row[\'name\']') < source.index('result = {')
    assert source.index('result = {') < source.index('_collect_verified_syntax(') < source.index('return result')
    assert 'canonical_message(result)' in source
    assert 'syntax_collector' not in inspect.getsource(audit.worker)


def test_callback_does_not_change_default_cli_or_expose_receipt_input():
    assert inspect.signature(audit.verify_in_fresh_windows).parameters['syntax_collector'].default is None
    main = inspect.getsource(audit.main)
    assert 'verify_in_fresh_windows()' in main
    assert not any(flag in main for flag in ('--receipt', '--render', '--skip', '--syntax'))


def test_reader_reuses_reviewed_transport_in_private_globals_and_preserves_defaults():
    pairs = (('_validate_render_message','_validate_render_message'),
             ('_read_rendered_files','_read_rendered_files'),
             ('_render_child','_render_child'),
             ('_reviewed_fork_render_phase','_fork_render_phase'))
    for new_name,old_name in pairs:
        new,old = getattr(reader,new_name),getattr(reader.old_transport,old_name)
        assert new is not old and new.__code__ is old.__code__
        assert new.__globals__ is reader.__dict__ and old.__globals__ is reader.old_transport.__dict__
        assert new.__defaults__ == old.__defaults__ and new.__kwdefaults__ == old.__kwdefaults__
        if new.__kwdefaults__ is not None:
            assert new.__kwdefaults__ is not old.__kwdefaults__
    assert reader.old_transport.audit is not reader.audit
    assert reader.audit.CPU_LIMITS == (170,175)
    assert reader.RENDER_WALL_SECONDS == 180 and reader.RENDER_TIMEOUT_SECONDS == 185
    assert reader.audit.MAX_RSS_BYTES == 1536*1024*1024
    assert reader.MAX_RENDER_MESSAGE_BYTES == 8192
    assert sha256(reader._source(ROOT/'scripts/build_constructive_dirichlet_explorer.py')).hexdigest() == reader.PRIOR_RENDER_SHA256


@pytest.mark.parametrize('entrypoint',('build_files','build_verified'))
def test_failed_real_inventory_gate_cannot_call_a_checker_renderer_or_writer(monkeypatch,tmp_path,entrypoint):
    def refuse():
        raise audit.support.PolynomialDivisionError('intentional final inventory rejection; no proof accepted')
    def forbidden(*_,**__):
        pytest.fail('a rejected inventory reached a proof or output operation')
    monkeypatch.setattr(reader.checkpoints,'require_final_inventory',refuse)
    monkeypatch.setattr(audit,'verify_in_fresh_windows',forbidden)
    monkeypatch.setattr(reader,'_fork_render_phase',forbidden)
    with pytest.raises(audit.support.PolynomialDivisionError,match='intentional final inventory rejection'):
        if entrypoint == 'build_files':
            reader.build_files()
        else:
            reader._build_verified(output=tmp_path/'never-created')
    assert list(tmp_path.iterdir()) == []


def test_reader_has_no_saved_receipt_or_render_only_entrypoint():
    source = inspect.getsource(reader._build_verified)
    assert source.index('proof_audit.verify_in_fresh_windows(') < source.index('_validate_live_report(')
    assert source.index('_validate_live_report(') < source.index('_fork_render_phase(')
    assert 'syntax_collector=collect' in source and 'write_audit=False' in source
    assert 'retained[0][2] != proof_audit.canonical_message(report)' in source
    assert tuple(inspect.signature(reader.build_files).parameters) == ()
    main = inspect.getsource(reader.main)
    assert not any(flag in main for flag in ('--receipt','--skip','--render-only','--saved','--reuse'))
    assert 'resource.setrlimit(resource.RLIMIT_CPU,proof_audit.CPU_LIMITS)' in main
    assert 'signal.alarm(CONTROLLER_WALL_SECONDS)' in main


def test_render_fingerprint_covers_actual_ui_drivers_definitions_atlas_and_old_transport():
    source = inspect.getsource(reader._render_binding)
    for name in ('CAMPAIGN_TEST_FILE','TEST_FILE','RFC','_definition_input_paths',
                 'extend_constructive_polynomial_division_campaign.py','constructive_polynomial_division_definitions.py',
                 'constructive_polynomial_division_definition_graph.py','test_constructive_bottom_layer_explorer.py',
                 'test_constructive_frontier_explorer.py','constructive_formula_compactor.py',
                 'constructive_bottom_layer_explorer_renderer.py','build_constructive_dirichlet_explorer.py'):
        assert name in source
    assert 'checkpoints.independent._check_lean_binary()' in source
    assert "'atlas':_atlas().source_binding()" in source
    assert 'support.PARENT_CATALOG_PINS' in source and 'support.MATH_SOURCE_PINS' in source
    assert 'del bundle' in inspect.getsource(reader._render_files)
    assert inspect.getsource(reader._render_files).index('del bundle') < inspect.getsource(reader._render_files).index('_atlas().build_files_for_verified_reader')


def test_definition_source_walk_covers_plain_and_from_imports_without_factories():
    """Independently enumerate the literal registry imports, not proof inputs."""
    pending = [ROOT/'scripts/constructive_polynomial_division_definitions.py',
               ROOT/'scripts/constructive_polynomial_division_definition_graph.py']
    expected = set()
    while pending:
        path = pending.pop()
        if path in expected:
            continue
        assert path.parent == ROOT/'scripts' and len(expected) < 64
        expected.add(path)
        for node in ast.walk(ast.parse(reader._source(path))):
            if isinstance(node,ast.Import):
                modules = [alias.name for alias in node.names]
            elif isinstance(node,ast.ImportFrom):
                modules = [node.module] if node.module else []
            else:
                continue
            for module in modules:
                if module.startswith('constructive_') and module.endswith(
                        ('_definitions','_definition_graph','_defined_adapter')):
                    pending.append(ROOT/'scripts'/(module+'.py'))
    actual = reader._definition_input_paths()
    assert type(actual) is tuple and actual == tuple(sorted(expected,key=str))
    assert {ROOT/'scripts'/name for name in (
        'constructive_g009_definitions.py','constructive_g009_definition_graph.py',
        'constructive_dirichlet_inverse_definitions.py','constructive_dirichlet_inverse_definition_graph.py',
        'constructive_first_wave_definition_graph.py','constructive_definition_graph.py')} <= expected
    source = inspect.getsource(reader._definition_input_paths)
    assert 'ast.Import' in source and 'ast.ImportFrom' in source and '>= 64' in source
    assert not any(name in source for name in ('load_candidate_state','all_new_rows','verify_checkpoint','replay_bottom'))


def test_render_binding_covers_executed_pytest_and_graph_observer_inputs():
    source = inspect.getsource(reader._render_binding)
    for name in ("ROOT/'conftest.py'","ROOT/'pytest.ini'","ROOT/'peano-lab/py/tests/conftest.py'",
                 'constructive_historical_graph_test_support.py','test_constructive_historical_publication_v31.py',
                 'defined_syntax.py','defined_edition.py','bertrand_defined_edition.py',
                 'book/_static/constructive-gaussian-factorization-explorer/gaussian-factorization/index.html'):
        assert name in source
    assert 'peano-lab/py/peano_lab/library' in source
    assert 'support._repository_path(path)' in source
    assert 'del bundle,target' in inspect.getsource(reader._render_files)
    body = inspect.getsource(reader._render_files)
    assert body.index('del bundle,target') < body.index('gc.collect()') < body.index('_atlas().build_files_for_verified_reader')


def test_family_contract_is_only_polynomial_prerequisites_and_keeps_G091_open():
    family = reader.family()
    assert (family.slug,family.prefix,family.domain,family.family_id,family.milestones) == (
        'polynomial-division-prerequisites','PQ','D04','F10',('G091',))
    assert family.roots == tuple(PRINCIPAL_CONTRACTS) == reader.checkpoints.PRINCIPAL_ROOTS
    assert family.goal_scope == 'polynomial_division_prerequisites_locally_proved_full_G091_open'
    for phrase in ('highest-degree-first','empty and all-zero','nonzero leading coefficient',
                   'unique in decoded values','General polynomial Euclidean division',
                   'gcd/Bezout','irreducible-polynomial existence','remain open','no Alpha or Stable admission'):
        assert phrase in family.caveat
    assert reader.SCHEMA == 'peano-lab-local-polynomial-division-proof-explorer-v1'
    assert reader.RENDER_SCHEMA == 'peano-lab-polynomial-division-fresh-render-v1'


def test_standalone_fixture_bootstraps_only_actual_verification_and_owns_returned_bytes():
    source = inspect.getsource(reader.fresh_test_snapshot)
    assert tuple(inspect.signature(reader.fresh_test_snapshot).parameters) == ()
    assert "Path(directory).resolve()/'files',return_snapshot=True" in source
    assert source.index('_build_verified(') < source.index('transport._decode_message(payload)')
    assert source.index('canonical_message(report) != payload') < source.index('files = dict(files)')
    assert source.index('files = dict(files)') < source.index('_validate_live_report(') < source.index('_assert_snapshot_binding(')
    assert source.index('_assert_snapshot_binding(') < source.index('peak_rss_bytes()') < source.index('return _FreshSnapshotTests(')
    for check in ('type(retained[0]) is not support.CandidateState',
                  'type(retained[1]) is not support.SupportSelection',
                  'type(retained[2]) is not bytes','type(files) is not dict',
                  'type(value) is not bytes',"worker_peak != report['peak_rss_bytes']",
                  'type(render_peak) is not int',"'proof-audit.json',SLUG+'/api/checkpoint.json'"):
        assert check in source
    assert not any(token in source for token in ('read_bytes(', 'read_text(', 'setrlimit(', 'signal.alarm(', 'pytest.main('))
    build = inspect.getsource(reader._build_verified)
    assert build.index('if type(return_snapshot) is not bool:') < build.index('_preflight_output(')
    assert build.index('_commit_tree(') < build.index('if return_snapshot:')
    assert "return result.files,report['peak_rss_bytes'],result.peak_rss_bytes,retained[0]" in build
    assert "return result.files,report['peak_rss_bytes'],result.peak_rss_bytes" in build
    fixture = inspect.getsource(live)
    assert "getattr(pytestconfig,'_polynomial_division_fresh_snapshot',None)" in fixture
    assert fixture.index('if plugin is None:') < fixture.index('reader.fresh_test_snapshot()') < fixture.index('assert type(plugin)')
    assert '_polynomial_division_fresh_snapshot = self' in inspect.getsource(reader._FreshSnapshotTests.pytest_configure)


@pytest.mark.parametrize('mode',(None,0,1,'true',(),{}))
def test_nonboolean_snapshot_return_mode_fails_before_any_input_or_output(monkeypatch,tmp_path,mode):
    monkeypatch.setattr(reader,'_render_binding',lambda:pytest.fail('invalid return mode reached source/proof inputs'))
    with pytest.raises(reader.ExplorerError,match='exact Boolean'):
        reader._build_verified(output=tmp_path.resolve()/'never-created',return_snapshot=mode)
    assert not tuple(tmp_path.iterdir())


@pytest.mark.parametrize('wrong',(False,True,{},SimpleNamespace(),object()))
def test_present_wrong_live_fixture_never_bootstraps_or_accepts(monkeypatch,wrong):
    monkeypatch.setattr(reader,'fresh_test_snapshot',lambda:pytest.fail('a present invalid plugin triggered a new run'))
    config = SimpleNamespace(_polynomial_division_fresh_snapshot=wrong)
    with pytest.raises(AssertionError,match='saved receipts are not fixtures'):
        live.__wrapped__(config)


def test_absent_live_fixture_propagates_a_real_bootstrap_refusal(monkeypatch):
    calls = []
    def refuse():
        calls.append('actual bootstrap refusal')
        raise reader.ExplorerError('intentional bootstrap failure; no proof accepted')
    monkeypatch.setattr(reader,'fresh_test_snapshot',refuse)
    with pytest.raises(reader.ExplorerError,match='intentional bootstrap failure'):
        live.__wrapped__(SimpleNamespace())
    assert calls == ['actual bootstrap refusal']


def test_real_bootstrap_inventory_failure_leaves_no_temporary_or_permanent_output(monkeypatch,tmp_path):
    def refuse():
        raise audit.support.PolynomialDivisionError('intentional inventory refusal before any proof')
    def forbidden(*_,**__):
        pytest.fail('a rejected bootstrap reached a proof or rendering operation')
    monkeypatch.setattr(reader,'OUTPUT',tmp_path.resolve()/'never-created')
    monkeypatch.setattr(reader.checkpoints,'require_final_inventory',refuse)
    monkeypatch.setattr(audit,'verify_in_fresh_windows',forbidden)
    monkeypatch.setattr(reader,'_fork_render_phase',forbidden)
    with pytest.raises(audit.support.PolynomialDivisionError,match='intentional inventory refusal'):
        reader.fresh_test_snapshot()
    assert not tuple(tmp_path.iterdir())


def _transport_manifest(files):
    """Literal display bytes only; this document contains no proof authority."""
    entries = {name:{'bytes':len(payload),'sha256':sha256(payload).hexdigest()}
               for name,payload in files.items() if name != 'manifest.json'}
    return reader._json({'schema':'transport-only-not-a-proof-manifest',
        'files':entries,'file_count_excluding_manifest':len(entries)})


@pytest.fixture
def nonauthority_ui_transport(monkeypatch):
    """Empty, unverified syntax for an always-rejected scheduler boundary.

    This fixture cannot pass the real live-report validator. The only stub is
    a non-verifying presentation fingerprint; no checker, audit, publication,
    output writer or source-selection function is replaced with success.
    """
    state = reader.support.CandidateState((),(),'TRANSPORT ONLY: NO THEOREMS')
    plan = reader.closure.BottomLayerPlan((),(),(),0,'NO ORDERED PROOF ROWS','NO FRONTIER')
    selected = reader.support.SupportSelection((),(),(),(),plan,())
    report = {'schema':'transport-only-not-a-proof-report',
              'notice':'No mathematical acceptance or fresh verification is represented.'}
    binding = '0'*64
    files = {'transport-page.html':b'<html><body>TRANSPORT ONLY; 0=1 is not a proof.</body></html>\n',
             'checkpoints.json':reader._json({'schema':'transport-only-not-evidence',
                                            'render_source_binding_sha256':binding})}
    files['manifest.json'] = _transport_manifest(files)
    monkeypatch.setattr(reader,'_render_binding',lambda:binding)
    return files,(state,selected,report)


def test_ui_transport_fixture_is_rejected_by_the_real_mathematical_evidence_guard(nonauthority_ui_transport):
    files,(state,selected,report) = nonauthority_ui_transport
    assert state.rows == selected.owned == selected.complete_specs == ()
    assert report['schema'] == 'transport-only-not-a-proof-report'
    with pytest.raises(reader.ExplorerError,match='retained exact 85-row/207-parent syntax'):
        reader._validate_live_report(report,state,selected)
    assert set(files) == {'transport-page.html','checkpoints.json','manifest.json'}


@pytest.mark.parametrize('attack',(
    'map_type','nontext_key','mutable_page','text_page','missing_manifest','manifest_not_object',
    'manifest_missing_row','manifest_extra_row','manifest_digest','manifest_size','manifest_count','manifest_count_bool',
    'page_changed','page_missing','extra_file',
))
def test_ui_scheduler_rejects_inconsistent_pretest_map_before_any_pytest(monkeypatch,nonauthority_ui_transport,attack):
    files,syntax = nonauthority_ui_transport
    if attack == 'map_type': files = tuple(files.items())
    elif attack == 'nontext_key': files[17] = b'TRANSPORT ONLY'
    elif attack == 'mutable_page': files['transport-page.html'] = bytearray(files['transport-page.html'])
    elif attack == 'text_page': files['transport-page.html'] = files['transport-page.html'].decode()
    elif attack == 'missing_manifest': files.pop('manifest.json')
    elif attack == 'manifest_not_object': files['manifest.json'] = b'[]\n'
    elif attack.startswith('manifest_'):
        if attack == 'manifest_count_bool':
            files.pop('transport-page.html')
            files['manifest.json'] = _transport_manifest(files)
        manifest = json.loads(files['manifest.json'])
        if attack == 'manifest_missing_row': manifest['files'].pop('transport-page.html')
        elif attack == 'manifest_extra_row': manifest['files']['missing-file.txt'] = {'bytes':1,'sha256':'0'*64}
        elif attack == 'manifest_digest': manifest['files']['transport-page.html']['sha256'] = '0'*64
        elif attack == 'manifest_size': manifest['files']['transport-page.html']['bytes'] += 1
        elif attack == 'manifest_count': manifest['file_count_excluding_manifest'] -= 1
        elif attack == 'manifest_count_bool': manifest['file_count_excluding_manifest'] = True
        else: raise AssertionError('unknown manifest attack')
        files['manifest.json'] = reader._json(manifest)
    elif attack == 'page_changed': files['transport-page.html'] = b'CHANGED TRANSPORT BYTES'
    elif attack == 'page_missing': files.pop('transport-page.html')
    elif attack == 'extra_file': files['extra.txt'] = b'UNEXPECTED TRANSPORT BYTES'
    else: raise AssertionError('unknown pretest map attack')
    monkeypatch.setattr(pytest,'main',lambda *_,**__:pytest.fail('inconsistent bytes reached a UI scheduler'))
    with pytest.raises(reader.RenderProcessError,match='immutable byte map|complete manifest'):
        reader._run_snapshot_tests(files,syntax)


@pytest.mark.parametrize('attack',(
    'page','page_removed','page_added','manifest','coherent_page_and_manifest','checkpoints',
    'equal_bytearray','equal_nontext_key','plugin_map','plugin_map_type','plugin_equal_bytearray',
    'plugin_binding','plugin_state','plugin_selection','report_in_place','plugin_report',
    'original_report_hidden_by_plugin_copy',
))
def test_ui_scheduler_never_accepts_posttest_ram_or_evidence_mutations(monkeypatch,nonauthority_ui_transport,attack):
    """A synthetic UI-only status reaches the real final guard, which must fail.

    The private input contains no proof or accepted report. No actual tests
    are simulated as proof checks, no outer pytest plugin is configured, and
    this function never calls a proof controller, renderer or output writer.
    Every scheduler path below intentionally corrupts its disposable input.
    """
    files,syntax = nonauthority_ui_transport
    called = []
    class TextSubclass(str):
        pass

    def corrupting_scheduler(arguments,*,plugins):
        assert arguments == ['-q',str(reader.TEST_FILE)] and len(plugins) == 1
        plugin = plugins[0]
        assert type(plugin) is reader._FreshSnapshotTests
        assert plugin.files is files and plugin.report is syntax[2]
        called.append(attack)
        # These explicit non-proof labels test completion transport only.
        names = ['TRANSPORT ONLY; NOT A TEST OR PROOF '+str(i) for i in range(reader.EXPECTED_READER_TESTS)]
        plugin.collected.extend(names)
        plugin.outcomes.extend((name,'passed',False) for name in names)
        if attack == 'page': files['transport-page.html'] = b'CHANGED AFTER UI; TRANSPORT ONLY'
        elif attack == 'page_removed': files.pop('transport-page.html')
        elif attack == 'page_added': files['extra.txt'] = b'ADDED AFTER UI; TRANSPORT ONLY'
        elif attack == 'manifest': files['manifest.json'] += b'\n'
        elif attack == 'coherent_page_and_manifest':
            files['transport-page.html'] = b'COHERENTLY REHASHED, BUT NOT THE INPUT BYTES'
            files['manifest.json'] = _transport_manifest(files)
        elif attack == 'checkpoints': files['checkpoints.json'] = b'{}\n'
        elif attack == 'equal_bytearray': files['transport-page.html'] = bytearray(files['transport-page.html'])
        elif attack == 'equal_nontext_key':
            value = files.pop('transport-page.html')
            files[TextSubclass('transport-page.html')] = value
        elif attack == 'plugin_map':
            object.__setattr__(plugin,'files',{**files,'transport-page.html':b'CHANGED PLUGIN MAP'})
        elif attack == 'plugin_map_type': object.__setattr__(plugin,'files',tuple(files.items()))
        elif attack == 'plugin_equal_bytearray':
            object.__setattr__(plugin,'files',{**files,'transport-page.html':bytearray(files['transport-page.html'])})
        elif attack == 'plugin_binding': object.__setattr__(plugin,'binding','1'*64)
        elif attack == 'plugin_state': object.__setattr__(plugin,'state',replace(syntax[0]))
        elif attack == 'plugin_selection': object.__setattr__(plugin,'selected',replace(syntax[1]))
        elif attack == 'report_in_place': plugin.report['notice'] = 'CHANGED UI TRANSPORT NOTICE'
        elif attack == 'plugin_report': object.__setattr__(plugin,'report',{**plugin.report,'changed':True})
        elif attack == 'original_report_hidden_by_plugin_copy':
            original = deepcopy(plugin.report)
            syntax[2]['notice'] = 'CHANGED ORIGINAL SHARED REPORT'
            object.__setattr__(plugin,'report',original)
        else: raise AssertionError('every UI scheduler path must corrupt its input')
        return 0

    monkeypatch.setattr(pytest,'main',corrupting_scheduler)
    with pytest.raises(reader.RenderProcessError,match='same-live pages or proof evidence'):
        reader._run_snapshot_tests(files,syntax)
    assert called == [attack]


def test_ui_scheduler_checks_full_map_before_and_after_actual_test_completion():
    source = inspect.getsource(reader._run_snapshot_tests)
    assert source.index('before = dict(files)') < source.index('expected_files =')
    assert source.index('expected_files =') < source.index('report_before =') < source.index('pytest.main(')
    assert source.index('pytest.main(') < source.index('_validate_test_completion(') < source.index('files != before')
    assert source.index('files != before') < source.index('return status')
    for field in ('plugin.files','plugin.binding','plugin.state','plugin.selected','plugin.report'):
        assert field in source[source.index('_validate_test_completion('):]


def test_observational_peak_is_not_serialized_as_a_fake_repeatable_measurement():
    # Formatting-only input, deliberately not the schema of any proof report.
    first = {'schema':'transport-only-not-proof-evidence','peak_rss_bytes':1,
             'notice':'No proof, output or successful audit is constructed.'}
    second = {**first,'peak_rss_bytes':reader.audit.MAX_RSS_BYTES}
    saved = deepcopy(first)
    left,right = reader._presentation_report(first),reader._presentation_report(second)
    assert first == saved and left == right
    assert 'peak_rss_bytes' not in left
    assert left['resource_policy'] == {'cpu_limits':[170,175],'wall_seconds_per_worker':180,
        'max_rss_bytes':1536*1024*1024,'observed_peak_within_limit':True,'observed_peak_serialized':False}
    assert left['proof_audit_schema'] == first['schema']
    assert left['schema'] != 'peano-polynomial-division-local-research-checkpoint-v1'


@pytest.mark.parametrize('peak',(None,False,True,0,-1,1.0,'1',1536*1024*1024+1))
def test_presentation_does_not_hide_a_failed_real_memory_bound(peak):
    with pytest.raises(reader.ExplorerError,match='real peak'):
        reader._presentation_report({'schema':'transport-only-no-proof','peak_rss_bytes':peak})


@pytest.mark.parametrize('route',('index.html','explorer/index.html','explorer/defined/tag/PQ0055.html'))
def test_intended_public_metadata_is_head_only_and_not_a_deployment_claim(route):
    # Literal formatting fixture, not a verified theorem or reader page.
    payload = b'<html><head><title>FORMAT ONLY &amp; not proof</title><script>const transportOnly=true;</script></head><body><pre>0=1\nnot a proof</pre><code>arbitrary  bytes\n</code></body></html>\n'
    path = reader.SLUG+'/'+route
    changed = reader._intended_public_metadata(path,payload)
    assert changed.split(b'</head>',1)[1] == payload.split(b'</head>',1)[1]
    assert b'<script>const transportOnly=true;</script>' in changed
    document = Document(changed)
    wanted = reader.PUBLIC_PROOFS_BASE+(path.removesuffix('index.html') if path.endswith('/index.html') else path)
    assert [attrs['href'] for tag,attrs in document.tags if tag == 'link' and attrs.get('rel') == 'canonical'] == [wanted]
    assert [attrs['content'] for tag,attrs in document.tags if tag == 'meta' and attrs.get('property') == 'og:url'] == [wanted]
    assert not any(word in changed for word in (b'published',b'Alpha-enrolled',b'HA checked'))


@pytest.mark.parametrize('path',('/index.html','other/index.html','polynomial-division-prerequisites/../index.html',
    'polynomial-division-prerequisites//index.html','polynomial-division-prerequisites/quote".html',
    'polynomial-division-prerequisites/index.html?x=1',None))
def test_public_metadata_rejects_foreign_or_unsafe_targets(path):
    with pytest.raises(reader.ExplorerError,match='safe HTML head'):
        reader._intended_public_metadata(path,b'<head><title>format only</title></head><body></body>')


def test_public_metadata_cannot_overwrite_an_inherited_canonical_identity():
    source = b'<head><title>format only</title><link rel="canonical" href="https://example.invalid/"></head><body>unchanged</body>'
    with pytest.raises(reader.ExplorerError,match='silently replaced'):
        reader._intended_public_metadata(reader.SLUG+'/index.html',source)


@pytest.fixture
def transport_tree(tmp_path):
    """Disposable literal bytes, not pages, proofs, reports or verification."""
    root = tmp_path.resolve()
    staged,destination = root/'staged',root/'destination'
    staged.mkdir()
    payload = b'TRANSPORT ONLY: no theorem, proof report, acceptance or publication.\n'
    (staged/'transport.txt').write_bytes(payload)
    return staged,destination,{'transport.txt':payload}


def test_atomic_primitive_is_the_byte_pinned_original_in_private_globals():
    function = reader._atomic_renamer()
    assert sha256(reader._source(reader.ATOMIC_RENAME_SOURCE)).hexdigest() == reader.ATOMIC_RENAME_SOURCE_SHA256
    assert function.__globals__ is not reader.__dict__
    assert function.__globals__['PublicationProcessError'] is reader.RenderProcessError
    assert set(function.__globals__) == {'ctypes','os','sys','Path','PublicationProcessError','__builtins__','_rename_new'}
    assert 'renamex_np' in inspect.getsource(function) and 'renameat2' in inspect.getsource(function)
    assert 'RENAME_EXCL' in inspect.getsource(function) and 'RENAME_NOREPLACE' in inspect.getsource(function)


def test_transport_only_tree_is_installed_after_both_actual_byte_and_callback_checks(transport_tree):
    source,destination,files = transport_tree
    identity = reader._directory_identity(source)
    seen = []
    def transport_check():
        seen.append((source.exists(),destination.exists()))
    reader._commit_tree(source,destination,files,check=False,final_check=transport_check)
    assert seen == [(True,False),(False,True)]
    assert not source.exists() and reader._directory_identity(destination) == identity
    assert (destination/'transport.txt').read_bytes() == files['transport.txt']


def test_transport_check_mode_compares_and_never_replaces_either_tree(transport_tree):
    source,destination,files = transport_tree
    destination.mkdir()
    (destination/'transport.txt').write_bytes(files['transport.txt'])
    identities = reader._directory_identity(source),reader._directory_identity(destination)
    calls = []
    reader._commit_tree(source,destination,files,check=True,final_check=lambda:calls.append('transport-only'))
    assert calls == ['transport-only','transport-only']
    assert identities == (reader._directory_identity(source),reader._directory_identity(destination))
    assert (destination/'transport.txt').read_bytes() == files['transport.txt']


@pytest.mark.parametrize('when',(1,2),ids=('before-install','after-install'))
def test_transport_callback_failure_leaves_no_target_and_recovers_owned_bytes(transport_tree,when):
    source,destination,files = transport_tree
    identity = reader._directory_identity(source)
    count = 0
    def refuse():
        nonlocal count
        count += 1
        if count == when:
            raise RuntimeError('transport-only bound/source gate refused')
    with pytest.raises(RuntimeError,match='transport-only bound/source gate refused'):
        reader._commit_tree(source,destination,files,check=False,final_check=refuse)
    assert count == when and not destination.exists()
    assert reader._directory_identity(source) == identity
    assert (source/'transport.txt').read_bytes() == files['transport.txt']


def test_native_atomic_rename_will_not_replace_an_existing_directory(transport_tree):
    source,destination,files = transport_tree
    destination.mkdir()
    (destination/'foreign.txt').write_bytes(b'FOREIGN TRANSPORT FIXTURE: preserve')
    with pytest.raises(OSError):
        reader._atomic_renamer()(source,destination)
    assert (destination/'foreign.txt').read_bytes() == b'FOREIGN TRANSPORT FIXTURE: preserve'
    assert (source/'transport.txt').read_bytes() == files['transport.txt']


def test_competing_target_before_install_is_not_overwritten(transport_tree):
    source,destination,files = transport_tree
    def competitor():
        destination.mkdir()
        (destination/'foreign.txt').write_bytes(b'FOREIGN TRANSPORT FIXTURE')
    with pytest.raises(reader.RenderProcessError,match='overwrite'):
        reader._commit_tree(source,destination,files,check=False,final_check=competitor)
    assert (destination/'foreign.txt').read_bytes() == b'FOREIGN TRANSPORT FIXTURE'
    assert (source/'transport.txt').read_bytes() == files['transport.txt']


def test_postinstall_failure_cannot_rollback_a_foreign_replacement(transport_tree):
    source,destination,files = transport_tree
    rescued = source.parent/'rescued-owned-transport'
    calls = 0
    def replace_after_install():
        nonlocal calls
        calls += 1
        if calls == 2:
            reader._atomic_renamer()(destination,rescued)
            destination.mkdir()
            (destination/'foreign.txt').write_bytes(b'FOREIGN TRANSPORT FIXTURE')
            raise RuntimeError('transport-only simulated postinstall failure')
    with pytest.raises(reader.RenderProcessError,match='rollback refused'):
        reader._commit_tree(source,destination,files,check=False,final_check=replace_after_install)
    assert (destination/'foreign.txt').read_bytes() == b'FOREIGN TRANSPORT FIXTURE'
    assert (rescued/'transport.txt').read_bytes() == files['transport.txt']


def test_native_permission_failure_is_not_retried_or_bypassed(monkeypatch,transport_tree):
    source,destination,files = transport_tree
    attempted = []
    def denied(old,new):
        attempted.append((old,new))
        raise PermissionError('synthetic denial for exact owned transport target')
    monkeypatch.setattr(reader,'_atomic_renamer',lambda:denied)
    with pytest.raises(PermissionError,match='synthetic denial'):
        reader._commit_tree(source,destination,files,check=False,final_check=lambda:None)
    assert attempted == [(source,destination)] and not destination.exists()
    assert (source/'transport.txt').read_bytes() == files['transport.txt']


def test_changed_bytes_immediately_after_native_move_cannot_be_installed(monkeypatch,transport_tree):
    source,destination,files = transport_tree
    native = reader._atomic_renamer()
    def moved_then_changed(old,new):
        native(old,new)
        if new == destination:
            (new/'transport.txt').write_bytes(b'CHANGED AFTER MOVE: transport fixture only')
    monkeypatch.setattr(reader,'_atomic_renamer',lambda:moved_then_changed)
    with pytest.raises(reader.ExplorerError):
        reader._commit_tree(source,destination,files,check=False,final_check=lambda:None)
    assert not destination.exists()
    assert (source/'transport.txt').read_bytes() == b'CHANGED AFTER MOVE: transport fixture only'


@pytest.mark.parametrize('attack',('changed','missing','extra','symlink'))
def test_changed_private_output_cannot_reach_installation(transport_tree,attack):
    source,destination,files = transport_tree
    if attack == 'changed':
        (source/'transport.txt').write_bytes(b'CHANGED TRANSPORT BYTES')
    elif attack == 'missing':
        (source/'transport.txt').unlink()
    elif attack == 'extra':
        (source/'extra.txt').write_bytes(b'UNEXPECTED TRANSPORT BYTES')
    else:
        (source/'extra-link').symlink_to(source/'transport.txt')
    with pytest.raises(reader.ExplorerError):
        reader._commit_tree(source,destination,files,check=False,
                            final_check=lambda:pytest.fail('changed bytes reached the final callback'))
    assert not destination.exists()


@pytest.mark.parametrize('attack',('changed','missing','extra'))
def test_stale_check_target_is_preserved_without_writes(transport_tree,attack):
    source,destination,files = transport_tree
    destination.mkdir()
    (destination/'transport.txt').write_bytes(files['transport.txt'])
    if attack == 'changed':
        (destination/'transport.txt').write_bytes(b'USER TRANSPORT EDIT')
    elif attack == 'missing':
        (destination/'transport.txt').unlink()
    else:
        (destination/'extra.txt').write_bytes(b'USER EXTRA TRANSPORT DATA')
    before = {path.name:path.read_bytes() for path in destination.iterdir()}
    with pytest.raises(reader.ExplorerError):
        reader._commit_tree(source,destination,files,check=True,final_check=lambda:None)
    assert before == {path.name:path.read_bytes() for path in destination.iterdir()}
    assert (source/'transport.txt').read_bytes() == files['transport.txt']


@pytest.mark.parametrize('kind',('directory','file','dangling-link'))
def test_creation_preflight_rejects_existing_targets_before_any_proof_job(monkeypatch,tmp_path,kind):
    target = tmp_path.resolve()/'existing'
    if kind == 'directory':
        target.mkdir()
    elif kind == 'file':
        target.write_bytes(b'EXISTING USER TRANSPORT FIXTURE')
    else:
        target.symlink_to(tmp_path/'missing')
    monkeypatch.setattr(reader,'_render_binding',lambda:pytest.fail('existing target reached proof inputs'))
    with pytest.raises(reader.RenderProcessError,match='overwrite'):
        reader._build_verified(output=target)
    assert target.is_symlink() if kind == 'dangling-link' else target.exists()


def test_creation_and_check_reject_symlink_ancestors(tmp_path):
    parent = tmp_path.resolve()/'regular'
    parent.mkdir()
    (parent/'existing').mkdir()
    alias = tmp_path.resolve()/'alias'
    alias.symlink_to(parent,target_is_directory=True)
    for check,name in ((False,'new'),(True,'existing')):
        with pytest.raises(reader.RenderProcessError,match='ancestor'):
            reader._preflight_output(alias/name,check=check)


def test_every_public_build_uses_private_output_and_mandatory_current_run_tests():
    source = inspect.getsource(reader._build_verified)
    tree = ast.parse(source)
    calls = [node for node in ast.walk(tree) if isinstance(node,ast.Call)
             and isinstance(node.func,ast.Name) and node.func.id == '_fork_render_phase']
    assert len(calls) == 1
    keywords = {item.arg:item.value for item in calls[0].keywords}
    assert isinstance(keywords['test'],ast.Constant) and keywords['test'].value is True
    assert isinstance(keywords['check'],ast.Constant) and keywords['check'].value is False
    assert isinstance(keywords['output'],ast.Name) and keywords['output'].id == 'staged'
    assert source.index('_preflight_output(') < source.index('verify_in_fresh_windows(')
    assert source.index('_fork_render_phase(') < source.index('_commit_tree(')
    assert 'test' not in inspect.signature(reader._build_verified).parameters
    assert "Path(directory).resolve()/'files'" in inspect.getsource(reader.build_files)
    assert 'args.test' not in inspect.getsource(reader.main)
    assert 'resource.setrlimit' in inspect.getsource(reader._reviewed_fork_render_phase)
    runner = inspect.getsource(reader._run_snapshot_tests)
    assert runner.index('pytest.main(') < runner.index('_validate_test_completion(') < runner.index('return status')
    assert 'PYTEST_ADDOPTS' not in runner and 'os.environ' not in runner


def test_public_builder_has_no_test_false_escape(tmp_path):
    with pytest.raises(TypeError):
        reader._build_verified(output=tmp_path.resolve()/'never-created',test=False)
    assert not tuple(tmp_path.iterdir())


@pytest.mark.parametrize('attack',('short','duplicate','foreign_path','collect_only','deselected','empty','list_names'))
def test_filtered_or_foreign_test_collection_metadata_fails_closed(attack):
    """Always-rejected scheduler metadata; no checker or proof fixture."""
    names = tuple('TRANSPORT-ONLY-NOT-PROOF-'+str(index) for index in range(reader.EXPECTED_READER_TESTS))
    paths = (reader.TEST_FILE.resolve(),)*reader.EXPECTED_READER_TESTS
    collect_only,rejected = False,()
    if attack == 'short': names = names[:-1]
    elif attack == 'duplicate': names = (*names[:-1],names[0])
    elif attack == 'foreign_path': paths = (*paths[:-1],Path('/transport-only/foreign-test.py'))
    elif attack == 'collect_only': collect_only = True
    elif attack == 'deselected': rejected = ('deselected',)
    elif attack == 'empty': names,paths = (),()
    else: names = list(names)
    with pytest.raises(reader.RenderProcessError,match='mandatory reader suite'):
        reader._validate_test_collection(names,paths,collect_only=collect_only,rejected=rejected)


@pytest.mark.parametrize('attack',('status','bool_status','missing_call','duplicate_call','skipped_call','xfail_call','failed_setup','collection_only'))
def test_partial_failed_or_skipped_test_outcomes_never_supply_success(attack):
    """Synthetic outcomes always rejected, never a fabricated live audit."""
    collected = tuple('TRANSPORT-ONLY-NOT-PROOF-'+str(index) for index in range(reader.EXPECTED_READER_TESTS))
    outcomes = tuple((name,'passed',False) for name in collected)
    status,rejected = 0,()
    if attack == 'status': status = 1
    elif attack == 'bool_status': status = False
    elif attack == 'missing_call': outcomes = outcomes[:-1]
    elif attack == 'duplicate_call': outcomes = (*outcomes[:-1],outcomes[0])
    elif attack == 'skipped_call': outcomes = (*outcomes[:-1],(collected[-1],'skipped',False))
    elif attack == 'xfail_call': outcomes = (*outcomes[:-1],(collected[-1],'passed',True))
    elif attack == 'failed_setup': rejected = ('failed setup',)
    else: outcomes = ()
    with pytest.raises(reader.RenderProcessError,match='did not all execute and pass'):
        reader._validate_test_completion(status,collected,outcomes,rejected)


@pytest.mark.parametrize('index',range(85),ids=lambda index:f'PQ{index+1:04X}')
def test_same_live_every_exact_statement_script_and_all_defined_local_asts(live,corpus,index):
    DOM['test_every_theorem_statement_script_and_all_local_propositions_are_exact'](
        reader.family(),live.state.rows[index],live.files,{reader.SLUG:corpus})


def test_same_live_exact_counts_roles_principals_and_non_admission(live,corpus):
    expected_names = [row.name for row in live.state.rows]
    assert len(expected_names) == len(set(expected_names)) == 85
    assert [row['name'] for row in corpus['nodes']] == expected_names
    assert corpus['tags'] == {name:f'PQ{index:04X}' for index,name in enumerate(expected_names,1)}
    assert corpus['root_names'] == list(reader.checkpoints.PRINCIPAL_ROOTS)
    assert corpus['tags'][corpus['root_names'][-1]] == 'PQ0055'
    assert corpus['node_count'] == corpus['new_theorem_count'] == 85
    assert corpus['complete_theorem_count'] == 292 and corpus['inherited_support_count'] == 207
    assert corpus['proof_bundle_node_count'] == 293
    assert corpus['parent_alpha_edition_version'] == 'v31'
    assert corpus['parent_alpha_checked_use_count'] == 3796 and corpus['parent_stable_count'] == 432
    assert all(corpus[key] == 0 for key in ('alpha_enrolled_node_count','alpha_checked_use_node_count','stable_admitted_node_count'))
    assert all(row['inventory_role'] == 'new_owned_theorem' for row in corpus['nodes'])
    for row in (corpus,*corpus['nodes']):
        assert reader.render._status(row) == reader.render.STATUS
        assert all(row[key] is False for key in reader.render.FORBIDDEN_ADMISSION_FIELDS)
        assert row['alpha_edition_version'] is row['alpha_first_enrolled_version'] is None
    assert live.report['fresh_worker_count'] == 8
    assert live.report['novelty']['exact_ast_novelty_checked'] is True
    assert live.report['novelty']['exact_statement_ast_duplicates'] == []
    assert live.report['novelty']['prior_theorems'] == 3886
    assert live.report['polynomial_prerequisite_principals_checked'] is True
    assert len(live.report['principal_roots']) == 6
    for record in live.report['principal_roots']:
        assert record['complete_ordinary_ha_checked'] is True
        assert type(record['ordinary_certificate_nodes']) is int and record['ordinary_certificate_nodes'] > 1


def test_same_live_owned_provenance_and_metrics_match_literal_checked_nodes(live,corpus):
    """Read the already checked literal bytes for display equality, not authority."""
    pin = reader.checkpoints.FINAL_ARTIFACT
    payload = live.files['checkpoints/'+Path(pin.path).name]
    assert len(payload) == pin.bytes and sha256(payload).hexdigest() == pin.sha256
    bundle,target = reader.decode_proof_bundle(payload.decode('utf-8'))
    assert len(bundle.nodes) == 293 and bundle.root == 292 and target == bundle.nodes[292].target
    assert sum(len(row.dependencies) for row in bundle.nodes) == pin.edges
    positions = {row.name:row.node_id for row in live.selected.plan.rows}
    offset = 0
    for owner,source in zip(reader.support.FACTORIES,live.state.sources,strict=True):
        for spec,node in zip(live.state.rows[offset:offset+owner.count],
                             corpus['nodes'][offset:offset+owner.count],strict=True):
            actual = bundle.nodes[positions[spec.name]]
            assert actual.target == parse_formula_with_names(spec.statement)[0]
            assert actual.dependencies == tuple(positions[name] for name in spec.dependencies)
            assert node['proof_bundle_node_id'] == actual.node_id
            assert node['proof_bundle_sha256'] == pin.sha256
            assert (node['body_proof_nodes'],node['body_proof_depth']) == reader.proof_metrics(actual.body)
            assert node['source_module'] == 'peano_lab.library.'+owner.module
            assert node['source_filename'] == owner.module+'.py' and node['factory'] == owner.factory
            assert node['sources'] == [{'source_module':node['source_module'],'factory':owner.factory,
                'source_sha256':source.sha256,'statement_sha256':sha256(spec.statement.encode()).hexdigest(),
                'script_sha256':sha256(('\n'.join(spec.script)+'\n').encode()).hexdigest(),'selected':True}]
        offset += owner.count
    assert offset == 85


REPORT_MUTATIONS = (
    'schema','full_goal_claim','principals_flag','worker_count','worker_bool','stored_receipt',
    'published','alpha','stable','rss_bool','bundle_ha','bundle_lean','bundle_nodes',
    'owned_missing','inherited_missing','principal_missing','principal_order','ordinary_unchecked',
    'ordinary_node','ordinary_statement','ordinary_count_bool','ordinary_extra','novelty','prior_count',
)


@pytest.mark.parametrize('attack',REPORT_MUTATIONS)
def test_same_live_reader_rejects_missing_or_changed_actual_evidence(live,attack):
    original = audit.canonical_message(live.report)
    changed = deepcopy(live.report)
    if attack == 'schema': changed['schema'] = 'not-this-fresh-audit'
    elif attack == 'full_goal_claim': changed['general_G091_prime_power_fields_proved'] = True
    elif attack == 'principals_flag': changed['polynomial_prerequisite_principals_checked'] = False
    elif attack == 'worker_count': changed['fresh_worker_count'] = 7
    elif attack == 'worker_bool': changed['fresh_worker_count'] = True
    elif attack == 'stored_receipt': changed['stored_receipt_is_proof_authority'] = True
    elif attack == 'published': changed['published'] = True
    elif attack == 'alpha': changed['alpha_admission_performed'] = True
    elif attack == 'stable': changed['stable_admission_performed'] = True
    elif attack == 'rss_bool': changed['peak_rss_bytes'] = True
    elif attack == 'bundle_ha': changed['checkpoint']['bundle']['original_ha_checked'] = False
    elif attack == 'bundle_lean': changed['checkpoint']['bundle']['independent_lean_checked'] = False
    elif attack == 'bundle_nodes': changed['checkpoint']['bundle']['nodes'] -= 1
    elif attack == 'owned_missing': changed['checkpoint']['owned_names'].pop()
    elif attack == 'inherited_missing': changed['checkpoint']['inherited_alpha_v31_names'].pop()
    elif attack == 'principal_missing': changed['principal_roots'].pop()
    elif attack == 'principal_order': changed['principal_roots'][0:2] = changed['principal_roots'][1::-1]
    elif attack == 'ordinary_unchecked': changed['principal_roots'][0]['complete_ordinary_ha_checked'] = False
    elif attack == 'ordinary_node': changed['principal_roots'][0]['node_id'] += 1
    elif attack == 'ordinary_statement': changed['principal_roots'][0]['statement_sha256'] = '0'*64
    elif attack == 'ordinary_count_bool': changed['principal_roots'][0]['ordinary_certificate_nodes'] = True
    elif attack == 'ordinary_extra': changed['principal_roots'][0]['assumed_success'] = True
    elif attack == 'novelty': changed['novelty']['exact_ast_novelty_checked'] = False
    elif attack == 'prior_count': changed['novelty']['prior_theorems'] = 3796
    else: raise AssertionError('an unknown evidence mutation would be vacuous')
    assert changed != live.report
    with pytest.raises(reader.ExplorerError):
        reader._validate_live_report(changed,live.state,live.selected)
    assert audit.canonical_message(live.report) == original


def test_same_live_progress_is_not_general_division_or_G091_closure(live,corpus,documents):
    assert corpus['campaign_goal_id'] == 'G091'
    assert corpus['campaign_goal_scope'] == 'polynomial_division_prerequisites_locally_proved_full_G091_open'
    assert corpus['published_atlas_changed'] is False
    inventory = strict_json(live.files['checkpoints.json'])
    assert inventory['polynomial_prerequisite_principals_checked'] is True
    assert inventory['general_G091_prime_power_fields_proved'] is False
    assert inventory['inherited_support_counted_as_new'] is False
    assert b'General G091 remains open.' in live.files['index.html']
    landing = live.files[reader.SLUG+'/index.html']
    for phrase in (b'General polynomial Euclidean division',b'gcd/Bezout',
                   b'irreducible-polynomial existence',b'remain open'):
        assert phrase in landing
    links = [attrs['href'] for tag,attrs in documents[reader.SLUG+'/index.html'].tags
             if tag == 'a' and 'href' in attrs]
    assert any('grand-campaign/' in href and parse_qs(urlsplit(href).query).get('focus') == ['G091'] for href in links)


def test_same_live_complete_inherited_theorems_have_literal_targets_and_real_anchors(live,corpus,documents):
    specs = {row.name:row for row in live.selected.complete_specs}
    own = {row.name for row in live.state.rows}
    inherited = corpus['external_dependencies']
    assert {row['name'] for row in inherited} == set(specs)-own
    assert len(inherited) == 207
    target = reader.SLUG+'/checkpoint.html'
    for row in inherited:
        source = specs[row['name']]
        assert row['statement'] == source.statement and row['script'] == list(source.script)
        assert row['dependencies'] == list(source.dependencies)
        assert row['statement_sha256'] == sha256(source.statement.encode()).hexdigest()
        assert row['script_sha256'] == sha256(('\n'.join(source.script)+'\n').encode()).hexdigest()
        assert row['inventory_role'] == 'inherited_alpha_v31'
        assert row['counted_as_new_owned_theorem'] is row['first_admission_reclassified'] is False
        assert row['alpha_checked_use'] is row['admitted_to_alpha'] is True
        assert row['reference_route'] == target+'#theorem-'+row['name']
        assert 'theorem-'+row['name'] in documents[target].ids
    for node in corpus['nodes']:
        assert set(node['dependencies']) <= own|set(corpus['external_theorem_routes'])


def test_same_live_conservative_definitions_three_typed_edges_and_proof_only_paths(live,corpus):
    DOM['test_definition_identity_exactness_and_acyclic_three_kind_dag'](
        reader.family(),{reader.SLUG:corpus},live.files)
    new = {row['name']:row for row in corpus['definitions']
           if row['id'].startswith('ND') and row['id'] >= 'ND0327'}
    assert set(new) == {row.name for row in reader.POLYNOMIAL_DIVISION_DEFINITIONS}
    assert len(new) == 7
    assert {row['id'] for row in new.values()} == {'ND'+str(index).zfill(4) for index in range(327,334)}
    assert {name:tuple(row['parameters']) for name,row in new.items()} == {
        'FpCoefficientNegation':('p','ab','ac','rb','rc','L'),
        'FpCoefficientSubtraction':('p','ab','ac','bb','bc','rb','rc','L'),
        'PolynomialSuffix':('b','c','t','d','e','M'),
        'FpPolynomialTrim':('p','b','c','L','t','d','e','M'),
        'FpMonic':('p','b','c','L'),
        'FpMonicNormalization':('p','k','ab','ac','bb','bc','L'),
        'FpSyntheticDivision':('p','b','c','a','n','qb','qc','r'),
    }
    assert not {'FpCanonicalCoefficients','FpCoefficientAdd','FpEuclideanDivision','PrimePowerField'} & new.keys()

PRINCIPAL_CONTRACTS = {
    'prime_field_polynomial_subtract_exists':
        'forall p ab ac bb bc l. Prime(p) -> BetaPrefixInto(ab,ac,l,p) -> BetaPrefixInto(bb,bc,l,p) -> exists rb rc. FpCoefficientSubtraction(p,ab,ac,bb,bc,rb,rc,l)',
    'prime_field_polynomial_trim_exists_unique':
        'forall p b c L. BetaPrefixInto(b,c,L,p) -> exists t d e M. FpPolynomialTrim(p,b,c,L,t,d,e,M) /\\ (forall u f g N. FpPolynomialTrim(p,b,c,L,u,f,g,N) -> (t=u /\\ (M=N /\\ BetaPrefixEqual(d,e,f,g,M))))',
    'prime_field_polynomial_monic_normalization_exists_unique':
        'forall p ab ac L d. Prime(p) -> FpRepresentedDegree(p,ab,ac,L,d) -> exists k bb bc. FpMonicNormalization(p,k,ab,ac,bb,bc,L) /\\ (FpMonic(p,bb,bc,L) /\\ (FpRepresentedDegree(p,bb,bc,L,d) /\\ (forall j cb cc. FpMonicNormalization(p,j,ab,ac,cb,cc,L) -> (j=k /\\ BetaPrefixEqual(cb,cc,bb,bc,L)))))',
    'prime_field_polynomial_synthetic_exists_unique':
        'forall p b c a n. Prime(p) -> BetaPrefixInto(b,c,S n,p) -> Lt(a,p) -> exists qb qc r. FpSyntheticDivision(p,b,c,a,n,qb,qc,r) /\\ (forall Qb Qc s. FpSyntheticDivision(p,b,c,a,n,Qb,Qc,s) -> (s=r /\\ BetaPrefixEqual(Qb,Qc,qb,qc,n)))',
    'prime_field_polynomial_synthetic_represented_degree':
        'forall p b c a n qb qc r. Prime(p) -> FpRepresentedDegree(p,b,c,S (S n),S n) -> FpSyntheticDivision(p,b,c,a,S n,qb,qc,r) -> FpRepresentedDegree(p,qb,qc,S n,n)',
    'prime_field_polynomial_synthetic_zero_remainder_iff':
        'forall p b c a n qb qc r. Prime(p) -> FpSyntheticDivision(p,b,c,a,n,qb,qc,r) -> ((r=0 -> FpHorner(p,b,c,a,S n,0)) /\\ (FpHorner(p,b,c,a,S n,0) -> r=0))',
}


@pytest.mark.parametrize('name',tuple(PRINCIPAL_CONTRACTS))
def test_independently_stated_six_principal_source_contracts(authored_rows,name):
    row = next(row for row in authored_rows if row.name == name)
    parser = _LocalDefinedParser(PRINCIPAL_CONTRACTS[name],DEFINITIONS)
    assert parser.parse() == parse_formula_with_names(row.statement)[0]
    assert not parser.free


def test_same_live_canonical_qr_landing_and_all_exact_defined_routes(live,corpus,documents):
    path = reader.SLUG+'/index.html'
    reference = ROOT/'book/_static/constructive-gaussian-factorization-explorer/gaussian-factorization/index.html'
    assert DOM['_landing_structure'](live.files[path]) == DOM['_landing_structure'](reference.read_bytes())
    assert sum('view-card' in attrs.get('class','').split() for _,attrs in documents[path].tags) == 3
    assert any(attrs.get('name') == 'robots' and attrs.get('content') == 'noindex' for _,attrs in documents[path].tags)
    assert [attrs['href'] for _,attrs in documents[path].tags if attrs.get('rel') == 'canonical'] == [reader.PUBLIC_PROOFS_BASE+reader.SLUG+'/']
    assert b'Alpha v31 remains 3796 theorems and Stable remains 432.' in live.files[path]
    assert b'Alpha v30 remains 3222' not in live.files[path]
    assert b'PQ0055.html' in live.files[path]
    for row in corpus['nodes']:
        for mode in ('explorer/tag','explorer/defined/tag'):
            assert reader.SLUG+'/'+mode+'/'+row['id']+'.html' in live.files
    for definition in corpus['definitions']:
        assert reader.SLUG+'/explorer/defined/definition/'+definition['id']+'.html' in live.files


@pytest.mark.parametrize('name',tuple(reader.ASSET_DIGESTS))
def test_same_live_five_canonical_assets_are_byte_identical(live,name):
    payload = live.files['assets/'+name]
    assert payload == reader.model.ASSET_SOURCES[name].read_bytes()
    assert sha256(payload).hexdigest() == reader.ASSET_DIGESTS[name]


@pytest.mark.parametrize('index',range(4))
def test_same_live_exact_mathematical_source_downloads(live,index):
    pin = live.state.sources[index]
    payload = live.files['sources/'+Path(pin.path).name]
    assert len(payload) == pin.bytes and sha256(payload).hexdigest() == pin.sha256
    assert payload == reader._source(reader.support.MATH_DIRECTORY/Path(pin.path).name)


def test_same_live_manifest_bundle_rfc_and_deterministic_audit_bytes(live,corpus):
    manifest = strict_json(live.files['manifest.json'])
    assert live.files['manifest.json'] == reader._json(manifest)
    assert set(manifest['files']) == set(live.files)-{'manifest.json'}
    assert manifest['file_count_excluding_manifest'] == len(live.files)-1
    for path,payload in live.files.items():
        assert not path.startswith('/') and not set(path.split('/'))&{'','..','.'} and '\\' not in path
        if path != 'manifest.json':
            assert manifest['files'][path] == {'bytes':len(payload),'sha256':sha256(payload).hexdigest()}
    pin = reader.checkpoints.FINAL_ARTIFACT
    assert live.files['checkpoints/'+Path(pin.path).name] == reader.closure._read_pinned(ROOT/pin.path,pin.bytes,pin.sha256)
    assert live.files['sources/'+reader.RFC.name] == reader._source(reader.RFC)
    presentation = reader._presentation_report(live.report)
    assert corpus['checkpoint_report'] == presentation
    assert live.files['proof-audit.json'] == live.files[reader.SLUG+'/api/checkpoint.json'] == audit.canonical_message(presentation)
    inventory = strict_json(live.files['checkpoints.json'])
    assert inventory['checkpoint'] == presentation and inventory['checkpoint']['resource_policy']['observed_peak_serialized'] is False
    assert inventory['new_theorems'] == 85 and inventory['inherited_alpha_v31_theorems'] == 207
    assert inventory['general_G091_prime_power_fields_proved'] is False
    assert inventory['published'] is inventory['alpha_admission_performed'] is inventory['stable_admission_performed'] is False
    saved = dict(inventory)
    digest = saved.pop('checkpoint_digest')
    assert digest == sha256(reader._json(saved)).hexdigest() == manifest['checkpoint_digest']


def test_same_live_every_html_link_and_fragment_resolves_without_invented_theorem_routes(live,documents):
    # Raw book snapshots are siblings of this additive reader. No existing
    # public or local research tree is overwritten by generation.
    logical_output = ROOT/'book/_static/constructive-polynomial-division-explorer'
    external_documents = {}
    for name,document in documents.items():
        assert len(document.ids) == len(set(document.ids)),name
        for tag,attrs in document.tags:
            for key in ('href','src'):
                if key not in attrs:
                    continue
                href = attrs[key]
                url = urlsplit(href)
                if url.scheme or url.netloc:
                    if attrs.get('rel') == 'canonical' and name.startswith(reader.SLUG+'/'):
                        route = name.removesuffix('index.html') if name.endswith('/index.html') else name
                        assert href == reader.PUBLIC_PROOFS_BASE+route
                    else:
                        assert name == 'grand-campaign/index.html' and url.scheme in {'http','https'},(name,href)
                    continue
                assert not url.path.startswith('/'),(name,href)
                decoded = unquote(url.path)
                assert '\\' not in decoded and '\x00' not in decoded,(name,href)
                target = posixpath.normpath(posixpath.join(posixpath.dirname(name),decoded)) if decoded else name
                if decoded.endswith('/'):
                    target = posixpath.normpath(target+'/index.html')
                if target.startswith('../'):
                    assert name == 'grand-campaign/index.html',(name,href)
                    destination = (logical_output/target).resolve()
                    assert destination.is_relative_to(ROOT/'book/_static') and destination.is_file(),(name,href,target)
                    if url.fragment:
                        if destination not in external_documents:
                            external_documents[destination] = Document(reader._source(destination))
                        assert unquote(url.fragment) in external_documents[destination].ids,(name,href)
                else:
                    assert target in live.files,(name,href,target)
                    if url.fragment:
                        assert target in documents and unquote(url.fragment) in documents[target].ids,(name,href)
                if name.startswith(reader.SLUG+'/') and decoded:
                    asset = Path(decoded).name
                    wanted = (reader.ASSET_DIGESTS[asset][:12] if tag in {'script','link'}
                              and asset in reader.render.ASSET_DIGESTS else reader.HTML_REVISION)
                    assert parse_qs(url.query).get('v') == [wanted],(name,href)


def test_same_live_all_inline_javascript_parses_and_embedded_graph_is_exact(live,documents):
    scripts = []
    for name,document in documents.items():
        for attrs,source in document.scripts:
            if attrs.get('type','').lower() in {'application/json','application/ld+json'}:
                strict_json(source)
            elif 'src' not in attrs:
                scripts.append({'name':name,'source':source})
            if attrs.get('id') == 'pa-defined-graph-data':
                assert source.startswith('window.PA_DEFINED_GRAPH=') and source.endswith(';')
                graph = strict_json(source[len('window.PA_DEFINED_GRAPH='):-1])
                assert graph == strict_json(live.files[name.replace('graph.html','api/graph.json')])
    for name,payload in live.files.items():
        if name.endswith('.js'):
            scripts.append({'name':name,'source':payload.decode()})
    assert len(scripts) >= 6
    program = 'const vm=require("node:vm"),rows=JSON.parse(require("node:fs").readFileSync(0,"utf8"));rows.forEach(x=>new vm.Script(x.source,{filename:x.name}));process.stdout.write(String(rows.length));'
    result = subprocess.run(['node','-e',program],input=json.dumps(scripts),text=True,
                            capture_output=True,timeout=20,check=True)
    assert int(result.stdout) == len(scripts)


def test_same_live_every_family_page_has_exact_intended_canonical_metadata(documents):
    for name,document in documents.items():
        if not name.startswith(reader.SLUG+'/'):
            continue
        route = name.removesuffix('index.html') if name.endswith('/index.html') else name
        expected = reader.PUBLIC_PROOFS_BASE+route
        assert [attrs['href'] for tag,attrs in document.tags if tag == 'link' and attrs.get('rel') == 'canonical'] == [expected]
        assert [attrs['content'] for tag,attrs in document.tags if tag == 'meta' and attrs.get('property') == 'og:url'] == [expected]


def _expected_graph_selection(graph,target,focus,*,complete_family,visible_definitions):
    """Independent typed selection of the real, untrimmed canonical graph."""
    nodes = {row['id']:row for row in graph['nodes']}
    assert len(nodes) == len(graph['nodes']) and target in nodes and focus in nodes
    kinds = {'proof_dependency':('theorem','theorem'),
             'uses_definition':('theorem','definition'),
             'definition_uses_definition':('definition','definition')}
    edges = graph['edges']
    assert len({(edge['source'],edge['target'],edge['kind']) for edge in edges}) == len(edges)
    for edge in edges:
        assert edge['kind'] in kinds and edge['source'] in nodes and edge['target'] in nodes
        assert (nodes[edge['source']]['kind'],nodes[edge['target']]['kind']) == kinds[edge['kind']]
    expected = {key for key,row in nodes.items() if row['kind'] == 'theorem'} if complete_family else {target}
    if not complete_family:
        for edge in edges:
            if edge['kind'] == 'proof_dependency' and target in (edge['source'],edge['target']):
                expected.update((edge['source'],edge['target']))
    pending = list(expected) if visible_definitions else [focus]
    if not visible_definitions:
        expected.add(focus)
    while pending:
        source = pending.pop()
        for edge in edges:
            if edge['kind'] != 'proof_dependency' and edge['source'] == source and edge['target'] not in expected:
                expected.add(edge['target'])
                pending.append(edge['target'])
    selected_edges = [edge for edge in edges if edge['source'] in expected and edge['target'] in expected]
    if not complete_family:
        path = graph['proof_adjacency'][target]['critical_root_path']
        assert type(path) is list and all(key in nodes and nodes[key]['kind'] == 'theorem' for key in path)
        route = set(zip(path,path[1:]))
        selected_edges = [edge for edge in selected_edges if focus in (edge['source'],edge['target'])
                          or edge['kind'] == 'proof_dependency' and (edge['source'],edge['target']) in route]
    return expected,len(selected_edges)


def _assert_graph_observation(graph,actual,target,focus,*,complete_family,visible_definitions):
    """Compact means no SVG links; a narrow observation must exercise real links."""
    expected,arrows = _expected_graph_selection(graph,target,focus,
        complete_family=complete_family,visible_definitions=visible_definitions)
    assert type(actual) is dict and set(actual) == graph_observer.REPORT_FIELDS
    assert type(actual['renderedNodeIds']) is list and len(actual['renderedNodeIds']) == len(expected)
    assert set(actual['renderedNodeIds']) == expected
    assert type(actual['renderedArrowCount']) is int and actual['renderedArrowCount'] == arrows
    assert actual['selectedNodeIds'] == [focus]
    node = next(row for row in graph['nodes'] if row['id'] == focus)
    assert actual['sidebarHref'] == node['href'] and actual['title'] == focus+' · '+node['name']
    assert actual['sidebarLabel'] == ('Open definition →' if node['kind'] == 'definition' else 'Open theorem →')
    assert actual['viewportRendered'] is True
    compact = len(expected) > 160
    assert complete_family or not compact, 'the actual narrow view must exercise nonempty SVG links'
    assert type(actual['compactNodeIds']) is list and len(set(actual['compactNodeIds'])) == len(actual['compactNodeIds'])
    assert set(actual['compactNodeIds']) == (expected if compact else set())
    assert type(actual['svgAnchorCount']) is int and actual['svgAnchorCount'] == (0 if compact else len(expected))
    if compact:
        assert actual['firstSvgHref'] is actual['svgHrefIsGetterOnly'] is actual['allSvgHrefsAreGetterOnly'] is None
    else:
        assert actual['svgAnchorCount'] > 0
        assert actual['firstSvgHref'] in {row['href'] for row in graph['nodes'] if row['id'] in expected}
        assert actual['svgHrefIsGetterOnly'] is actual['allSvgHrefsAreGetterOnly'] is True
    parameters = parse_qs(urlsplit(actual['currentAddress']).query)
    assert parameters['target'] == [target] and parameters['focus'] == [focus]
    assert parameters['view'] == ['corpus' if complete_family else 'neighborhood']
    assert parameters['definitions'] == ['visible' if visible_definitions else 'selected']
    assert parameters['edges'] == ['all' if complete_family else 'focus']


@pytest.mark.parametrize('kind',('theorem','definition'))
def test_same_live_actual_graph_handles_getter_only_svg_links_and_focus(live,kind):
    graph = strict_json(live.files[reader.SLUG+'/api/graph.json'])
    target = graph['root_ids'][-1]
    focus = target if kind == 'theorem' else next(row['id'] for row in graph['nodes'] if row['kind'] == 'definition')
    for complete_family in (True,False):
        actual = graph_observer.observe_graph(graph,target,focus,
            complete_family=complete_family,visible_definitions=False)
        _assert_graph_observation(graph,actual,target,focus,
            complete_family=complete_family,visible_definitions=False)
        if complete_family:
            assert {row['id'] for row in graph['nodes'] if row['kind'] == 'theorem'} <= set(actual['renderedNodeIds'])
            assert actual['renderedArrowCount'] > 0


def test_same_live_actual_graph_definition_visibility_and_three_edge_kinds(live):
    graph = strict_json(live.files[reader.SLUG+'/api/graph.json'])
    target = graph['root_ids'][-1]
    expected = {row['id'] for row in graph['nodes'] if row['kind'] == 'theorem'}
    while True:
        additional = {edge['target'] for edge in graph['edges']
                      if edge['kind'] != 'proof_dependency' and edge['source'] in expected}
        if additional <= expected:
            break
        expected.update(additional)
    actual = graph_observer.observe_graph(graph,target,target,complete_family=True,visible_definitions=True)
    _assert_graph_observation(graph,actual,target,target,complete_family=True,visible_definitions=True)
    assert set(actual['renderedNodeIds']) == expected
    assert actual['renderedArrowCount'] == sum(edge['source'] in expected and edge['target'] in expected for edge in graph['edges'])
    assert graph['parent_alpha_edition_version'] == 'v31' and graph['parent_alpha_checked_use_count'] == 3796
    narrow = graph_observer.observe_graph(graph,target,target,complete_family=False,visible_definitions=False)
    _assert_graph_observation(graph,narrow,target,target,complete_family=False,visible_definitions=False)
    assert narrow['svgAnchorCount'] > 0


def test_same_live_exact_navigation_never_injects_a_missing_graph(live,documents):
    cases = []
    for name,document in documents.items():
        if '/explorer/' not in name or '/defined/' in name:
            continue
        links = [attrs['href'] for tag,attrs in document.header_tags if tag == 'a' and 'data-graph-navigation' in attrs]
        assert len(links) == 1 and 'defined/graph.html' in links[0],name
        page = next(attrs['data-page'] for tag,attrs in document.tags if tag == 'body')
        cases.append({'name':name,'page':page,'href':links[0]})
    assert len(cases) == 86
    source = live.files['assets/exact-explorer.js'].decode()
    start = source.index('  function initializeGraphNavigation()')
    end = source.index('\n  function ',start+1)
    program = '''const vm=require("node:vm"),input=JSON.parse(require("node:fs").readFileSync(0,"utf8"));
input.cases.forEach(row=>{
 const anchor={getAttribute(){return row.href;}};
 const header={querySelector(selector){if(selector==="[data-graph-navigation]")return anchor;throw Error(selector);}};
 const document={body:{dataset:{page:row.page}},querySelector(selector){if(selector===".pa-proof-header")return header;throw Error(selector);},createElement(){throw Error("bad graph injection in "+row.name);}};
 vm.runInNewContext(input.source+"\\ninitializeGraphNavigation();",{document});
});process.stdout.write(String(input.cases.length));'''
    result = subprocess.run(['node','-e',program],input=json.dumps({'source':source[start:end],'cases':cases}),
                            text=True,capture_output=True,timeout=20,check=True)
    assert int(result.stdout) == 86


@pytest.mark.parametrize('ready_state',('loading','complete'))
@pytest.mark.parametrize('canonical_first',(False,True))
def test_same_live_dashboard_search_kind_layer_count_clear_under_both_load_orders(live,corpus,ready_state,canonical_first):
    DOM['test_actual_canonical_dashboard_and_local_addon_combine_all_three_filters'](
        reader.family(),ready_state,canonical_first,live.files,{reader.SLUG:corpus})


def test_same_live_defined_proof_lines_highlight_initial_hash_and_focus_on_change(live,corpus):
    DOM['test_actual_defined_reader_highlights_initial_fragment_and_focuses_hash_changes'](
        reader.family(),live.files,{reader.SLUG:corpus})


def test_same_live_actual_detail_overlay_never_promotes_a_new_theorem(live):
    DOM['test_actual_graph_detail_overlay_never_calls_a_local_theorem_alpha_checked'](
        reader.family(),live.files)


@pytest.mark.parametrize('field',reader.render.FORBIDDEN_ADMISSION_FIELDS)
@pytest.mark.parametrize('value',(True,1,None))
def test_same_live_local_renderer_rejects_admission_and_ambiguous_flags(corpus,field,value):
    with pytest.raises(reader.render.LocalExplorerRenderError):
        reader.render._status({**corpus,field:value})


@pytest.mark.parametrize('field',('local_checkpoint_verified','original_ha_bundle_verified','independent_lean_bundle_verified'))
def test_same_live_local_renderer_cannot_drop_a_real_verification(corpus,field):
    with pytest.raises(reader.render.LocalExplorerRenderError):
        reader.render._status({**corpus,field:False})


@pytest.mark.parametrize('field',('alpha_first_enrolled_version','alpha_edition_version','alpha_evidence','first_admitted_version'))
def test_same_live_local_renderer_rejects_false_new_alpha_identity(corpus,field):
    with pytest.raises(reader.render.LocalExplorerRenderError):
        reader.render._status({**corpus,field:'v32'})


def test_same_live_atlas_preserves_all_goal_statuses_and_exact_current_alpha_boundary(live,corpus):
    files = {name.removeprefix('grand-campaign/'):payload for name,payload in live.files.items()
             if name.startswith('grand-campaign/')}
    _atlas_test_module().assert_same_live_campaign(files,corpus,live.report,live.state,live.selected)


@pytest.mark.parametrize('attack',_atlas_mutations())
def test_same_live_atlas_rejects_each_changed_postseal_proof_or_presentation_fact(live,corpus,attack):
    _atlas_test_module().assert_same_live_evidence_rejected(corpus,live.report,live.state,live.selected,attack)
