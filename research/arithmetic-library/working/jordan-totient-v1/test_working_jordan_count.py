"""Real source/old-cone guards, and reject-only I/O/protocol seams; no proofs."""
import ast
from dataclasses import replace
from pathlib import Path
import sys
import pytest

HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE))
import working_jordan_count_support as support
import check_working_jordan_count as checker


def test_exact_complete_cone_preserves_all_old238_records():
    owned,rows,roots=support.source_selection(86)
    old_owned,old_rows,_=support.prior.source_selection(75)
    assert owned[:75]==old_owned and len(owned)==86
    byname={r.name:r for r in rows}
    assert len(rows)==270 and sum(len(r.dependencies) for r in rows)==690
    assert all(byname[r.name]==r for r in old_rows) and len(old_rows)==238
    seen=set()
    for r in rows:
        assert set(r.dependencies)<=seen
        seen.add(r.name)
    assert roots==support.PRINCIPALS and len(roots)==5
    assert not any(n.startswith('peano_lab.library.editions') for n in sys.modules)


@pytest.mark.parametrize('bad',[True,False,75,85,87,'86',None])
def test_only_exact_stage86(bad):
    with pytest.raises(ValueError):support.stage_path(bad)


def test_real_prior_binding_and_two_seed_pins():
    assert support.prior.state_binding()==support.PRIOR_BINDING
    assert support.state_binding()==support.state_binding()
    paths=support.required_seeds(86)
    assert paths==tuple(support.ROOT/p.path for p in support.SEEDS)
    assert paths[0]==support.prior.stage_path(75)
    assert paths[1].name=='working-cyclic-units-proof-bundle-v1.json'
    for p in support.SEEDS:assert support.actual_pin(support.ROOT/p.path)==p


@pytest.mark.parametrize('index',[0,1])
def test_changed_real_seed_rejects_without_any_proof(index):
    with pytest.raises(ValueError):support.read_pin(replace(support.SEEDS[index],sha256='0'*64))


@pytest.mark.parametrize('field',['statement','dependencies','script','summary'])
def test_actual_new_source_mutation_is_rejected(field,monkeypatch):
    original=support._new_sources;rows=original();row=rows[-1]
    values=dict(statement='0=1',dependencies=row.dependencies+('zero_add',),
                script=row.script+('refl',),summary=row.summary+' changed')
    changed=rows[:-1]+(replace(row,**{field:values[field]}),)
    monkeypatch.setattr(support,'_new_sources',lambda:changed)
    with pytest.raises(ValueError):support.source_selection(86)


def test_cycle_and_foreign_source_ownership_rejected(monkeypatch):
    rows=support._new_sources();last=rows[-1]
    monkeypatch.setattr(support,'_new_sources',lambda:rows[:-1]+(replace(last,dependencies=(last.name,)),))
    with pytest.raises(ValueError,match='cycle'):support.source_selection(86)
    monkeypatch.setattr(support,'_new_sources',lambda:(replace(rows[0],name='zero_add'),)+rows[1:])
    with pytest.raises(ValueError,match='overlap'):support.source_selection(86)


def test_absent_registration_rejected_before_source_work(monkeypatch):
    monkeypatch.setattr(checker,'FINAL_ARTIFACT',None)
    def forbidden():raise AssertionError('source work before registration rejection')
    monkeypatch.setattr(support,'state_binding',forbidden)
    with pytest.raises(ValueError,match='no actual final artifact'):
        checker.run('bundle',86,artifact_sha='0'*64)


@pytest.mark.parametrize('kind',['exists','symlink','wrong-name'])
def test_exclusive_output_boundary_precedes_source_work(tmp_path,monkeypatch,kind):
    monkeypatch.setattr(support,'ARTIFACT_DIRECTORY',tmp_path)
    target=tmp_path/'preserved';target.write_bytes(b'owned by user')
    path=support.stage_path(86)
    if kind=='exists':path.write_bytes(b'existing artifact')
    elif kind=='symlink':path.symlink_to(target)
    else:path=tmp_path/'other.json'
    def forbidden():raise AssertionError('source work before output rejection')
    monkeypatch.setattr(support,'state_binding',forbidden)
    with pytest.raises(ValueError):checker.run('author',86,output=path)
    assert target.read_bytes()==b'owned by user'
    if kind=='exists':assert path.read_bytes()==b'existing artifact'


@pytest.mark.parametrize('name',['jordan_totient_count_unique','not_a_root',None])
def test_final_roots_are_exact_not_intermediate_aliases(name,monkeypatch):
    def forbidden():raise AssertionError('source work before root rejection')
    monkeypatch.setattr(support,'state_binding',forbidden)
    with pytest.raises(ValueError):checker.run('root',86,artifact_sha='0'*64,name=name)


def functions(path):
    return {n.name:n for n in ast.parse(path.read_text()).body if isinstance(n,ast.FunctionDef)}


@pytest.mark.parametrize('name',['resources','directory_identity','destination','write_exclusive','parent_pins'])
def test_security_routes_exact_original_ast(name):
    a=functions(HERE/'check_working_jordan.py')[name]
    b=functions(HERE/'check_working_jordan_count.py')[name]
    assert ast.dump(a)==ast.dump(b)


def test_original_complete_proof_routes_and_single_clock():
    text=ast.unparse(functions(HERE/'check_working_jordan_count.py')['run'])
    for s in ('closure.assemble_bottom_layer_bundle','closure.check_bottom_layer_bundle',
              'independent._lean_check(checkpoint, receipt.node_count, bundle.root, payload)',
              'closure.replay_bottom_layer_theorem','check((), proof.certificate, formula)',
              'batch_size=1','support.seed_coverage(through)'):
        assert s in text
    assert text.index('destination(through, output)')<text.index('support.state_binding()')
    assert text.count('parent_pins(closure)')==3
    for name in ('check_working_jordan_count.py','export_working_jordan_count.py'):
        source=(HERE/name).read_text()
        assert 'resource.setrlimit(resource.RLIMIT_CPU,(170,175));signal.alarm(180)' in source
        assert 'observations-v1.json' not in source
    assert 'checker.STARTED=STARTED' in (HERE/'export_working_jordan_count.py').read_text()
    assert support.MAX_BYTES==67108864


def test_source_targets_and_ordered_premises_are_both_required():
    source=ast.unparse(functions(HERE/'working_jordan_count_support.py')['execution_selection'])
    assert '_closed_formula(old.statement) == _closed_formula(row.statement)' in source
    assert 'old.dependencies == row.dependencies' in source
    assert 'row.dependencies == exact.dependencies' in source
    assert 'closure.bottom_layer_plan(frontier)' in source
    coverage=ast.unparse(functions(HERE/'working_jordan_count_support.py')['seed_coverage'])
    assert 'len(targets) == 259' in coverage
    assert 'prior.source.inert_seed_coverage' in coverage
    assert "not result['missing_names']" in coverage


def test_runtime_provider_is_original_pinned_not_a_local_substitute():
    pins=support.prior.json.loads(support.prior.raw(HERE/'original-runtime-byte-pins-v1.json'))
    # The actual manifest shape is inspected rather than trusting a copied pin.
    assert 'fermat_two_squares_pigeonhole_candidate.py' in str(pins)
    source=(HERE/'working_jordan_count_support.py').read_text()
    assert "importlib.import_module('peano_lab.library.fermat_two_squares_pigeonhole_candidate')" in source
    assert 'observations-v1.json' not in source
