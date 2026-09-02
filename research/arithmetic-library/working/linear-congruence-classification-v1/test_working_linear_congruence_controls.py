"""Non-authorizing syntax/rejection guards; no successful fake proof fixtures."""
import ast
from dataclasses import replace
from hashlib import sha256
import json
from pathlib import Path
import sys

import pytest

HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE))
import working_linear_congruence_support as support
import export_working_linear_congruence as exporter
import check_working_linear_congruence as checker

def test_exact_source_inventory_and_dfs():
    selected=support.select_support()
    assert (len(selected.owned),len(selected.inherited),len(selected.complete_specs))==(12,202,214)
    assert sum(len(r.dependencies) for r in selected.complete_specs)==642
    assert support.spec_digest(selected.complete_specs)=='9f79e853ba97569237492f8db46a6ec3f8d0c10dd21b54083b3f3633712cfba1'
    assert support.closure._specs_digest(selected.owned)=='b1128492a1dd801ec81f63a39f586f733e95b79a1d2a19d33bb0363130d560c8'
    assert selected.root_names==support.PRINCIPAL_ROOTS
    available=set()
    for row in selected.complete_specs:
        assert set(row.dependencies)<=available
        available.add(row.name)

@pytest.mark.parametrize('field,value',[('statement','0=0'),('dependencies',()),('script',()),('summary','foreign'),('name','foreign')])
def test_changed_mathematical_row_rejected(field,value):
    rows=list(support.candidate_rows());rows[0]=replace(rows[0],**{field:value})
    with pytest.raises(ValueError,match='altered source'):support.select_support(tuple(rows))

@pytest.mark.parametrize('value',[None,(),[],{},'receipt',True,12])
def test_foreign_final_registration_is_rejected(monkeypatch,value):
    monkeypatch.setattr(checker,'FINAL_ARTIFACT',value)
    with pytest.raises(ValueError,match='no actual final'):checker.require_final_inventory()

@pytest.mark.parametrize('field,value',[('path','../foreign'),('path','/tmp/foreign'),('path','research/foreign.json'),
    ('bytes',True),('bytes',0),('bytes',support.MAX_BYTES+1),('nodes',214),('nodes',True),('edges',646),
    ('body_nodes',0),('sha256','0'),('sha256',None)])
def test_malformed_final_registration_rejected_before_read(monkeypatch,field,value):
    pin=checker.ArtifactPin(support.stage_path().relative_to(support.ROOT).as_posix(),1,'0'*64,215,647,1)
    monkeypatch.setattr(checker,'FINAL_ARTIFACT',replace(pin,**{field:value}))
    with pytest.raises(ValueError,match='malformed/partial'):checker.require_final_inventory()

@pytest.mark.parametrize('name',[None,'','saved-success','mod_eq_cancel_gcd_cofactor',True])
def test_only_maximal_principals_enter_native_route(name):
    with pytest.raises(ValueError,match='unknown ordinary'):checker.verify_principal(name)

@pytest.mark.parametrize('through',[None,True,0,11,13,'12'])
def test_unregistered_stage_is_rejected(through):
    with pytest.raises(ValueError,match='unregistered'):support.stage_path(through)

@pytest.mark.parametrize('path',['foreign.json','/tmp/foreign.json','artifacts/../foreign.json'])
def test_foreign_output_is_rejected(path):
    with pytest.raises(ValueError):exporter.destination(path)

@pytest.mark.parametrize('field,value',[('path','../bad'),('bytes',0),('bytes',True),('sha256','bad')])
def test_malformed_source_pin_is_rejected(field,value):
    with pytest.raises(ValueError,match='malformed exact'):support.read_pin(replace(support.SOURCE_PIN,**{field:value}))

def test_final_unset_fails_closed_even_after_source_success(monkeypatch):
    support.select_support()
    monkeypatch.setattr(checker,'FINAL_ARTIFACT',None)
    with pytest.raises(ValueError,match='no actual final'):checker.verify_complete_bundle()

def functions(path):
    return {n.name:n for n in ast.parse(path.read_bytes()).body if isinstance(n,(ast.FunctionDef,ast.AsyncFunctionDef))}

def calls(node):
    return [ast.unparse(n.func) for n in ast.walk(node) if isinstance(n,ast.Call)]

def test_original_routes_and_literal_limits_preserved():
    exp=functions(HERE/'export_working_linear_congruence.py')
    chk=functions(HERE/'check_working_linear_congruence.py')
    assert 'support.closure.assemble_bottom_layer_bundle' in calls(exp['export_authoring_bundle'])
    assert 'support.closure.check_bottom_layer_bundle' in calls(chk['verify_complete_bundle'])
    assert 'support.independent._lean_check' in calls(chk['verify_complete_bundle'])
    assert 'support.closure.replay_bottom_layer_theorem' in calls(chk['verify_principal'])
    assert 'check' in calls(chk['verify_principal'])
    for path in (HERE/'export_working_linear_congruence.py',HERE/'check_working_linear_congruence.py'):
        tree=ast.parse(path.read_bytes())
        limits=[n for n in ast.walk(tree) if isinstance(n,ast.Call) and ast.unparse(n.func)=='resource.setrlimit']
        assert len(limits)==1 and ast.literal_eval(limits[0].args[1])==(170,175)
        alarm=[n for n in ast.walk(tree) if isinstance(n,ast.Call) and ast.unparse(n.func)=='signal.alarm']
        assert len(alarm)==1 and ast.literal_eval(alarm[0].args[0])==180
        assert 'peano_lab.library.editions' not in path.read_text()

def test_same_authenticated_payload_goes_to_original_lean():
    node=functions(HERE/'check_working_linear_congruence.py')['verify_complete_bundle']
    call=next(n for n in ast.walk(node) if isinstance(n,ast.Call) and ast.unparse(n.func)=='support.independent._lean_check')
    assert ast.unparse(call.args[-1])=='payload'
    text=ast.unparse(node)
    assert text.index('check_bottom_layer_bundle')<text.index('_lean_check')<text.index('_finish')

def test_exclusive_owned_inode_and_source_rollback_guards_present():
    node=functions(HERE/'export_working_linear_congruence.py')['write_exclusive']
    text=ast.unparse(node)
    for token in ('os.O_EXCL','os.O_NOFOLLOW','os.O_CLOEXEC','os.O_DIRECTORY','os.fstat','os.getuid',
                  'st_nlink','created','os.unlink','support.state_binding() == binding'):
        assert token in text
    assert 'except BaseException' in text

def test_source_dfs_never_substituted_for_original_artifact_order():
    node=functions(HERE/'working_linear_congruence_support.py')['execution_selection']
    text=ast.unparse(node)
    assert 'closure.parent_snapshot' in text and 'closure.bottom_layer_plan(frontier)' in text
    assert 'row.dependencies == expected.dependencies' in text
    assert 'row.statement_sha256 == sha256(expected.statement.encode()).hexdigest()' in text

def test_no_record_or_report_is_read_as_proof_authority():
    for path in (HERE/name for name in support.CONTROL_FILES[:3]):
        text=path.read_text()
        assert 'focused-' not in text and 'conditional-verification-observations' not in text
        assert 'monkeypatch' not in text

def test_actual_runtime_pin_manifest_authenticates_only_existing_sources():
    pins=support.runtime_manifest()
    assert all(pin.path.endswith('.py') for pin in pins)
    assert len(pins)==len({pin.path for pin in pins})
    for module,_ in support.PROVIDERS:
        assert 'peano-lab/py/peano_lab/library/'+module+'.py' in {p.path for p in pins}
    assert 'scripts/constructive_bottom_layer_checkpoints.py' in {p.path for p in pins}
    assert 'peano-lab/py/peano_lab/kernel/checker.py' in {p.path for p in pins}

def test_observation_reports_have_explicit_non_admission_flags():
    for path in (HERE/'export_working_linear_congruence.py',HERE/'check_working_linear_congruence.py'):
        text=path.read_text()
        assert 'alpha_admission_performed=False' in text
        assert 'stable_admission_performed=False' in text
        assert 'complete_checkpoint_acceptance=False' in text
