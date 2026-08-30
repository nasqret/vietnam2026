"""Independent contracts, real-beta diagnostics and original-HA block bodies."""

from dataclasses import replace
from functools import lru_cache
import gc
import re

import pytest

from peano_lab.library import signed_block_sum_candidate as candidate
from peano_lab.library.candidate_validation import CandidateBodyError, replay_candidate_bodies
from peano_lab.library.theorems import TheoremSpec, _closed_formula
from tests.test_divisor_sum_table_candidate import _assert_same_ast
from tests.test_signed_rectangular_slice_candidate import (
    expected_table, expected_entry, expected_sum, expected_slice, expected_slice_sum,
    _instantiate, actual_sum_trace,
)
from tests.test_signed_rectangular_sums_candidate import (
    core as previous_core, rows as rectangle_rows, expected_rows, expected_rectangle,
)
from tests.test_signed_table_operations_candidate import (
    expected_signed_operation, model_table, model_at, model_sum, encode_signed, decode_signed,
)


def conjunction(*formulas):
    if len(formulas) == 1:
        return formulas[0]
    return '('+formulas[0]+') /\\ ('+conjunction(*formulas[1:])+')'


def iff(first, second):
    return conjunction(f'({first}) -> ({second})',f'({second}) -> ({first})')


def operation(a,b,c,tag,*,multiply):
    return _instantiate(expected_signed_operation('LEFT','RIGHT','RESULT',multiply=multiply),
                        {'LEFT':a,'RIGHT':b,'RESULT':c},tag)


@lru_cache(maxsize=1)
def rows():
    return candidate.make_signed_block_sum_candidate_theorems(TheoremSpec)


@lru_cache(maxsize=1)
def core():
    return previous_core() | {row.name:row for row in rectangle_rows()}


def checked(row, table):
    try:
        return replay_candidate_bodies((row,),core=table)[0]
    except CandidateBodyError as error:
        pytest.fail(str(error)[:700],pytrace=False)
    finally:
        gc.collect()


EXPECTED=((57,22),(89,27),(320,47),(71,31),(238,50),(116,28),(29,17))


@pytest.mark.parametrize('row',rows(),ids=lambda row:row.name)
def test_original_ha_body(row):
    receipt = checked(row,core() | {item.name:item for item in rows()})
    assert (receipt.proof_nodes,receipt.proof_depth)==EXPECTED[rows().index(row)]
    assert 0<receipt.proof_objects<=receipt.proof_nodes and receipt.proof_depth<=256


@pytest.mark.parametrize('row',rows(),ids=lambda row:row.name)
def test_false_target_is_rejected(row):
    with pytest.raises(CandidateBodyError):
        replay_candidate_bodies((replace(row,statement='0=1'),),core=core() | {item.name:item for item in rows()})
    gc.collect()


EDGES=tuple((row,dependency) for row in rows() for dependency in row.dependencies)


@pytest.mark.parametrize('row,dependency',EDGES,ids=lambda value:value.name if hasattr(value,'name') else value)
@pytest.mark.parametrize('change',('drop','poison'))
def test_every_declared_dependency_is_required(row,dependency,change):
    gc.collect()
    table=core() | {item.name:item for item in rows()}
    if change=='drop':
        row=replace(row,dependencies=tuple(name for name in row.dependencies if name!=dependency))
    else:
        table[dependency]=replace(table[dependency],statement='0=1')
    with pytest.raises(CandidateBodyError):
        replay_candidate_bodies((row,),core=table)
    gc.collect()


def test_native_order_and_all_dependencies_are_really_used():
    available=set(core())
    assert len(rows())==7
    assert sum(len(row.dependencies) for row in rows())==39
    assert sum(len(row.script) for row in rows())==470
    for row in rows():
        assert row.name not in available and len(set(row.dependencies))==len(row.dependencies)
        assert set(row.dependencies)<=available
        assert all(re.search(r"(?<![\w'])"+re.escape(name)+r"(?![\w'])",'\n'.join(row.script)) for name in row.dependencies)
        assert not any(command.startswith(('use ','admit','sorry','DNE','ring')) for command in row.script)
        _closed_formula(row.statement)
        available.add(row.name)


def contracts():
    source=expected_table('0','F','source')
    first=expected_slice_sum('F','o','s','p','a','first')
    tail=expected_slice_sum('F','o+s*p','s','q','b','tail')
    total=expected_slice_sum('F','o','s','p+q','c','total')
    add=operation('a','b','c','add',multiply=False)
    return {
        'signed_slice_identity': f'forall F l. ({source}) -> ({expected_slice("F","F","0","1","l","identity")})',
        'signed_slice_sum_unit_prefix_iff': f'forall F l z. ({source}) -> '+iff(expected_slice_sum('F','0','1','l','z','slice'),expected_sum('F','l','z','prefix')),
        'signed_slice_sum_concatenate': f'forall q F o s p a b c. ({first}) -> ({tail}) -> ({add}) -> ({total})',
        'signed_slice_sum_concatenate_values': f'forall F o s p q a b c. ({first}) -> ({tail}) -> ({total}) -> ({add})',
        'signed_row_sums_flatten': 'forall m F R n z. ('+expected_rows('F','R','0','n','1','m','n','rows')+') -> ('+expected_sum('R','m','z','sum')+') -> ('+expected_slice_sum('F','0','1','m*n','z','flat')+')',
        'signed_prefix_sum_row_major_iff': f'forall F m n z. ({source}) -> '+iff(expected_sum('F','m*n','z','prefix'),expected_rectangle('F','0','n','1','m','n','z','rectangle')),
        'signed_prefix_sum_row_major_exists': f'forall F m n. ({source}) -> exists z. '+conjunction(expected_sum('F','m*n','z','prefix'),expected_rectangle('F','0','n','1','m','n','z','rectangle')),
    }


@pytest.mark.parametrize('row',rows(),ids=lambda row:row.name)
def test_every_statement_has_an_independent_expanded_contract(row):
    _assert_same_ast(_closed_formula(row.statement),_closed_formula(contracts()[row.name]))


@pytest.mark.parametrize('offset,stride,p,q',((0,1,0,0),(7,0,0,4),(2,0,3,4),(1,1,4,0),(3,2,2,3),(0,3,3,2)))
def test_actual_beta_affine_concatenation_including_zero_stride(offset,stride,p,q):
    extent=offset+stride*max(p+q-1,0)+1
    values=tuple(((-1)**i)*(i+2) for i in range(extent))
    source=model_table(values,offset=7,endpoint=991)
    first=tuple(decode_signed(model_at(source,offset+stride*i)) for i in range(p))
    second=tuple(decode_signed(model_at(source,(offset+stride*p)+stride*j)) for j in range(q))
    combined=tuple(decode_signed(model_at(source,offset+stride*k)) for k in range(p+q))
    assert combined==first+second
    a=actual_sum_trace(model_table(first,offset=3,endpoint=71),p)
    b=actual_sum_trace(model_table(second,offset=8,endpoint=-71),q)
    c=actual_sum_trace(model_table(combined,offset=11,endpoint=999),p+q)
    assert decode_signed(c)==decode_signed(a)+decode_signed(b)


@pytest.mark.parametrize('m,n',((0,0),(0,3),(4,0),(1,1),(2,3),(3,2),(3,3)))
def test_actual_beta_flattened_prefix_equals_actual_row_fold(m,n):
    values=tuple(((-1)**k)*(k+1) for k in range(m*n))
    source=model_table(values,offset=5,endpoint=913)
    row_values=[]
    for i in range(m):
        entries=tuple(decode_signed(model_at(source,n*i+j)) for j in range(n))
        row_values.append(decode_signed(actual_sum_trace(model_table(entries,offset=4+i,endpoint=-919),n)))
    rows_table=model_table(row_values,offset=13,endpoint=997)
    assert actual_sum_trace(source,m*n)==actual_sum_trace(rows_table,m)==encode_signed(sum(values))
    assert model_at(source,m*n)==encode_signed(913)


def test_wrong_block_offset_and_included_endpoint_are_not_valid_bridges():
    values=(2,-3,7,5,11,13,17)
    source=model_table(values,endpoint=999)
    p,q,offset,stride=2,1,0,2
    correct=sum(values[offset+stride*i] for i in range(p+q))
    wrong=sum(values[offset+stride*i] for i in range(p))+sum(values[offset+p+stride*j] for j in range(q))
    assert correct!=wrong
    assert model_sum(source,6)!=model_sum(source,7)


def test_exact_novelty_against_all3796_prior_rows():
    import constructive_dirichlet_inverse_support as support
    from peano_lab.library import dirichlet_signed_unit_candidate, dirichlet_triangular_candidate, dirichlet_inverse_candidate
    old40=tuple(row for module in (dirichlet_signed_unit_candidate,dirichlet_triangular_candidate,dirichlet_inverse_candidate)
                for row in getattr(module,'make_'+module.__name__.rsplit('.',1)[1].replace('_candidate','')+'_candidate_theorems')(TheoremSpec))
    assert len(old40)==40 and support.PRIOR_THEOREM_COUNT==3756
    assert support.statement_duplicates((*old40,*rows()))==()
