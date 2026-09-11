"""Focused source/path/rejection guards; no successful proof mocks or replay."""
import ast
from dataclasses import replace
from hashlib import sha256
import importlib.util
from pathlib import Path
import sys
import pytest

HERE=Path(__file__).parent
sys.path.insert(0,str(HERE))
import working_jordan_support as support
import check_working_jordan as checker


@pytest.mark.parametrize('through,nodes,edges,roots',[(51,205,498,6),(69,232,569,13),(75,238,587,4)])
def test_actual_complete_source_cones(through,nodes,edges,roots):
    owned,rows,maximal=support.source_selection(through)
    assert len(owned)==through and len(rows)==nodes
    assert sum(len(r.dependencies) for r in rows)==edges and len(maximal)==roots
    seen=set()
    for row in rows:
        assert set(row.dependencies)<=seen
        seen.add(row.name)
    assert set(r.name for r in owned)<=seen
    assert not any(n.startswith('peano_lab.library.editions') for n in sys.modules)


@pytest.mark.parametrize('bad',[True,False,0,50,52,68,70,74,76,'75',None])
def test_exact_stage_boundary_rejects(bad):
    with pytest.raises(ValueError):support.stage_path(bad)


def test_actual_original_runtime_and_math_binding():
    before=support.state_binding()
    assert len(before)==64 and before==support.state_binding()


def test_conservative_stage_seed_chain():
    assert support.required_seeds(51)==tuple(support.ROOT/p.path for p in support.SEEDS)
    assert support.required_seeds(69)==(support.stage_path(51),support.ROOT/support.SEEDS[1].path,support.ROOT/support.SEEDS[2].path)
    assert support.required_seeds(75)==(support.stage_path(69),)


@pytest.mark.parametrize('field,value',[('bytes',True),('bytes',0),('bytes',67108865),('sha256','x'*64),('path','../wrong')])
def test_malformed_literal_seed_pins_reject(field,value):
    with pytest.raises(ValueError):support.read_pin(replace(support.SEEDS[0],**{field:value}))


def test_changed_real_seed_pin_rejects_before_any_proof():
    with pytest.raises(ValueError,match='literal bytes changed'):
        support.read_pin(replace(support.SEEDS[0],sha256='0'*64))


def test_raw_link_rejection(tmp_path):
    p=tmp_path/'file';p.write_bytes(b'first')
    link=tmp_path/'link';link.symlink_to(p)
    with pytest.raises(ValueError):support.raw(link)
    parent=tmp_path/'linked';parent.symlink_to(tmp_path,target_is_directory=True)
    with pytest.raises(ValueError):support.raw(parent/'file')


def test_actual_inplace_change_during_read_rejects(tmp_path,monkeypatch):
    path=tmp_path/'changing';path.write_bytes(b'first')
    original=support.os.fstat;calls=[]
    def mutate_after_first_stat(fd):
        value=original(fd);calls.append(fd)
        if len(calls)==1:path.write_bytes(b'changed bytes')
        return value
    monkeypatch.setattr(support.os,'fstat',mutate_after_first_stat)
    with pytest.raises(ValueError,match='changed during authenticated read'):support.raw(path)


def test_final_artifact_is_explicitly_absent_for_this_guard(monkeypatch):
    monkeypatch.setattr(checker,'FINAL_ARTIFACT',None)
    with pytest.raises(ValueError,match='no actual final artifact'):checker.verify_registration(75,'0'*64)
    def forbidden():raise AssertionError('parent/source work before missing registration rejection')
    monkeypatch.setattr(support,'state_binding',forbidden)
    with pytest.raises(ValueError,match='no actual final artifact'):checker.run('bundle',75,artifact_sha='0'*64)


@pytest.mark.parametrize('name',['unknown','jordan_totient_exists',None])
def test_only_exact_four_final_roots_are_admissible(name,monkeypatch):
    def forbidden():raise AssertionError('source work before name rejection')
    monkeypatch.setattr(support,'state_binding',forbidden)
    with pytest.raises(ValueError):checker.run('root',75,artifact_sha='0'*64,name=name)


def test_existing_output_rejected_before_parent_or_source_work(tmp_path,monkeypatch):
    monkeypatch.setattr(support,'ARTIFACT_DIRECTORY',tmp_path)
    path=support.stage_path(51);path.write_bytes(b'user-owned-existing')
    def forbidden():raise AssertionError('source work before output rejection')
    monkeypatch.setattr(support,'state_binding',forbidden)
    with pytest.raises(ValueError,match='never overwritten'):checker.run('author',51,output=path)
    assert path.read_bytes()==b'user-owned-existing'


def test_output_link_and_other_stage_rejected(tmp_path,monkeypatch):
    monkeypatch.setattr(support,'ARTIFACT_DIRECTORY',tmp_path)
    target=tmp_path/'other';target.write_bytes(b'preserve')
    support.stage_path(51).symlink_to(target)
    with pytest.raises(ValueError):checker.destination(51,support.stage_path(51))
    with pytest.raises(ValueError):checker.destination(69,support.stage_path(75))
    assert target.read_bytes()==b'preserve'


@pytest.mark.parametrize('kind',['statement','dependency','script','summary'])
def test_actual_source_record_mutations_reject(kind,monkeypatch):
    owned,core,providers=support.source.inventory()
    row=owned[-1]
    changes={'statement':{'statement':'0=1'},'dependency':{'dependencies':row.dependencies+('zero_add',)},
             'script':{'script':row.script+('refl',)},'summary':{'summary':row.summary+' changed'}}
    bad=replace(row,**changes[kind]);changed=owned[:-1]+(bad,);core=dict(core);core[row.name]=bad
    monkeypatch.setattr(support.source,'inventory',lambda:(changed,core,providers))
    with pytest.raises(ValueError):support.source_selection(75)


def test_proof_routes_are_original_and_same_byte():
    tree=ast.parse((HERE/'check_working_jordan.py').read_text())
    functions={n.name:n for n in tree.body if isinstance(n,ast.FunctionDef)}
    text=ast.unparse(functions['run'])
    assert 'closure.assemble_bottom_layer_bundle' in text
    assert 'closure.check_bottom_layer_bundle' in text
    assert 'independent._lean_check(checkpoint, receipt.node_count, bundle.root, payload)' in text
    assert 'closure.replay_bottom_layer_theorem' in text
    assert 'check((), proof.certificate, formula)' in text
    assert 'batch_size=1' in text
    assert 'decode_proof_bundle(payload.decode())' in text
    assert text.index('destination(through, output)')<text.index('support.state_binding()')
    assert text.index('original_parent_pins = parent_pins(closure)')<text.index('support.execution_selection(through)')
    assert text.count('parent_pins(closure)')==3
    pins=ast.unparse(functions['parent_pins'])
    assert 'closure.PARENT_CATALOG_SHA256' in pins and 'closure.parent_snapshot().documents' in pins
    assert 'support.read_pin(pin)' in pins


def test_original_caps_and_no_acceptance_from_saved_reports():
    text=(HERE/'check_working_jordan.py').read_text()
    assert 'resource.setrlimit(resource.RLIMIT_CPU,(170,175));signal.alarm(180)' in text
    assert 'complete_checkpoint_acceptance=False' in text and 'alpha_admitted=False' in text
    assert 'observations-v1.json' not in text
    support_text=(HERE/'working_jordan_support.py').read_text()
    assert 'observations-v1.json' not in support_text
    assert support.MAX_BYTES==64*1024*1024


def test_exclusive_writer_has_owned_inode_rollback():
    tree=ast.parse((HERE/'check_working_jordan.py').read_text())
    function=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='write_exclusive')
    text=ast.unparse(function)
    for flag in ('os.O_EXCL','os.O_NOFOLLOW','os.O_DIRECTORY','os.O_CLOEXEC'):assert flag in text
    assert '(info.st_dev, info.st_ino) == created' in text
    assert 'os.unlink(path.name, dir_fd=directory)' in text
