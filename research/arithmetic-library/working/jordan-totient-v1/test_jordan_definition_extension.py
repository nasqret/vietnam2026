"""Actual expansion/identity/parent tests, with no theorem or Alpha imports."""
from dataclasses import replace
from pathlib import Path
import sys
import pytest

HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE));sys.path.insert(0,str(HERE.parents[3]/'scripts'))
import jordan_definition_extension as adapter
from constructive_polynomial_gcd_definitions_v34 import ALL_CONSTRUCTIVE_DEFINITIONS_BY_NAME as PREVIOUS
from peano_lab.kernel.formulas import parse_formula_in_context


@pytest.mark.parametrize('index',range(11))
def test_exact_frozen_builder_and_renamed_argument_contract(index):
    base,rectangle=adapter._sources()
    builders=(base._all_dvd,base._primitive,base._pointwise_mod,base._enumeration,
              base._jordan,base._listed,base._scan,base._representatives,base._crt_tuple,base._canonical_crt,rectangle._rect)
    d=adapter.definitions()[index];builder=builders[index]
    assert d.stable_id==f'ND{371+index:04d}'
    assert d.template_formula==parse_formula_in_context(builder(*d.parameters,'independent'),list(d.parameters))
    args=tuple('free'+str(i) for i in range(d.arity))
    assert d.template_formula==parse_formula_in_context(builder(*args,'different'),list(args))


def test_actual407_parent_objects_digest_and_typed_dag_preserved():
    before=adapter.registry_digest(PREVIOUS);snapshot=tuple(PREVIOUS.items())
    result=adapter.extend_registry(PREVIOUS)
    assert len(PREVIOUS)==407 and len(result)==418
    assert all(result[name] is d for name,d in snapshot)
    assert before==adapter.registry_digest(PREVIOUS)
    seen=set(PREVIOUS)
    for d in adapter.definitions():
        assert set(d.conceptual_dependencies)<=seen
        seen.add(d.name)
    edges=adapter.definition_edges()
    assert edges and all(e['kind']=='definition_uses_definition' for e in edges)
    with pytest.raises(TypeError):result['foreign']=next(iter(PREVIOUS.values()))
    assert not any(n.startswith('peano_lab.library.editions') for n in sys.modules)


def test_exact_historical_zero_difference_tuple_equality_mapping():
    base,_=adapter._sources();d=PREVIOUS['IntegerVectorZero']
    assert d.stable_id=='ND0121' and d.parameters==('ab','ac','db','dc','l')
    params=('b','c','d','e','k')
    assert d.template_formula==parse_formula_in_context(base._equal(*params,'mapping'),list(params))
    result=adapter.extend_registry(PREVIOUS)
    assert result['IntegerVectorZero'] is d
    assert all(x.stable_id!='ND0370' for x in result.values())


@pytest.mark.parametrize('kind',['name','id','missing-parent','duplicate-id','equivalent-alias'])
def test_caller_registry_conflicts_fail_closed(kind):
    prior=dict(PREVIOUS);d=adapter.definitions()[0]
    if kind=='name':prior[d.name]=d
    elif kind=='id':prior['Foreign']=replace(d,name='Foreign')
    elif kind=='missing-parent':prior.pop('BetaAt')
    elif kind=='duplicate-id':prior['Foreign']=replace(next(iter(prior.values())),name='Foreign')
    else:prior['Foreign']=replace(d,name='Foreign',stable_id='ND9999')
    with pytest.raises(ValueError):adapter.extend_registry(prior)


def test_jordan_literal_count_graph_is_not_product_identity():
    base,_=adapter._sources();definitions={d.name:d for d in adapter.definitions()}
    assert definitions['JordanTotient'].conceptual_dependencies==('JordanTupleEnumeration',)
    assert definitions['JordanTupleEnumeration'].arity==7
    assert definitions['JordanRectangleCRT'].arity==18
    assert base._jordan('k','n','j','independent').count('exists')>0
    # Primitive tuple is separate from canonical range; neither is an oracle.
    assert definitions['JordanPrimitiveTuple'].conceptual_dependencies==('Dvd','JordanTupleAllDivisible')
    assert 'BetaPrefixInto' not in definitions['JordanPrimitiveTuple'].conceptual_dependencies
