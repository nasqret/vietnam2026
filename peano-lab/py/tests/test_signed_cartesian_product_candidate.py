"""Independent actual outer-product contracts, hygiene and hostile HA cases."""

from dataclasses import replace
from functools import lru_cache
import gc
import re

import pytest

from peano_lab.library import signed_cartesian_product_candidate as candidate
from peano_lab.library.candidate_validation import CandidateBodyError, replay_candidate_bodies
from peano_lab.library.theorems import TheoremSpec, _closed_formula
from tests.test_divisor_sum_table_candidate import _assert_same_ast
from tests.test_signed_block_sum_candidate import (
    core as block_core, rows as block_rows, checked, conjunction, operation,
    expected_table, expected_entry, expected_sum, expected_slice, expected_slice_sum,
    expected_rows, expected_rectangle, actual_sum_trace,
    model_table, model_at, encode_signed, decode_signed,
)


@lru_cache(maxsize=1)
def rows():
    return candidate.make_signed_cartesian_product_candidate_theorems(TheoremSpec)


@lru_cache(maxsize=1)
def core():
    return block_core() | {row.name:row for row in block_rows()}


def lt(a,b,tag):
    return f'exists independent_gap_{tag}. independent_gap_{tag}+S ({a})=({b})'


def le(a,b,tag):
    return f'exists independent_gap_{tag}. independent_gap_{tag}+({a})=({b})'


def mul(a,b,c,tag):
    return operation(a,b,c,tag,multiply=True)


def expected_product(F,G,T,m,n,tag):
    i,j,a,b,c=('independent_'+role+'_'+tag for role in ('row','column','left','right','value'))
    entry=(f'forall {i} {j} {a} {b} {c}. ({lt(i,m,tag+"row")}) -> ({lt(j,n,tag+"column")}) -> '
           f'({expected_entry(F,i,a,tag+"left")}) -> ({expected_entry(G,j,b,tag+"right")}) -> '
           f'({expected_entry(T,f"({n})*{i}+{j}",c,tag+"output")}) -> ({mul(a,b,c,tag+"multiply")})')
    return conjunction(expected_table('0',F,tag+'F'),expected_table('0',G,tag+'G'),
                       expected_table(f'({m})*({n})',T,tag+'T'),entry)


def expected_flat_entry(F,G,n,k,z,tag):
    i,j,a,b=('independent_flat_'+role+'_'+tag for role in ('row','column','left','right'))
    return f'exists {i} {j} {a} {b}. '+conjunction(f'({k})=({n})*{i}+{j}',lt(j,n,tag+'remainder'),
        expected_entry(F,i,a,tag+'first'),expected_entry(G,j,b,tag+'second'),mul(a,b,z,tag+'result'))


def expected_flat_prefix(F,G,n,l,T,tag):
    i,z='independent_index_'+tag,'independent_value_'+tag
    return conjunction(expected_table(l,T,tag+'table'),f'forall {i} {z}. ({le(i,l,tag+"bound")}) -> '
                       f'({expected_entry(T,i,z,tag+"lookup")}) -> ({expected_flat_entry(F,G,n,i,z,tag+"entry")})')


def expected_equal(F,G,l,tag):
    i,a,b=('independent_equal_'+role+'_'+tag for role in ('index','left','right'))
    return (f'forall {i} {a} {b}. ({lt(i,l,tag+"bound")}) -> '
            f'({expected_entry(F,i,a,tag+"first")}) -> ({expected_entry(G,i,b,tag+"second")}) -> {a}={b}')


def expected_scale(a,F,G,l,tag):
    i,b,c=('independent_scale_'+role+'_'+tag for role in ('index','left','right'))
    entry=f'forall {i}. ({lt(i,l,tag+"bound")}) -> exists {b} {c}. '+conjunction(
        expected_entry(F,i,b,tag+'first'),expected_entry(G,i,c,tag+'second'),mul(a,b,c,tag+'result'))
    return conjunction(expected_table(l,F,tag+'F'),expected_table(l,G,tag+'G'),entry)


def expected_coordinates(m,n,k,tag):
    i,j='independent_row_'+tag,'independent_column_'+tag
    return f'exists {i} {j}. '+conjunction(f'({k})=({n})*{i}+{j}',lt(i,m,tag+'row'),lt(j,n,tag+'column'))


def contracts():
    P=lambda F='F',G='G',T='T',m='m',n='n',tag='product':expected_product(F,G,T,m,n,tag)
    E=lambda k,z,tag:expected_flat_entry('F','G','n',k,z,tag)
    Q=lambda l,T,tag:expected_flat_prefix('F','G','n',l,T,tag)
    F0=expected_table('0','F','F0');G0=expected_table('0','G','G0')
    first=expected_sum('F','m','a','sumF');second=expected_sum('G','n','b','sumG')
    rect=expected_rectangle('T','0','n','1','m','n','c','sumRect')
    prefix=expected_sum('T','m*n','c','sumT');result=mul('a','b','c','signed_result')
    return {
        'signed_cartesian_flat_entry_exists': f'forall F G n k. ({F0}) -> ({G0}) -> ~(n=0) -> exists z. ({E("k","z","entry")})',
        'signed_cartesian_flat_entry_lookup': f'forall F G n i j a b z. ({lt("j","n","bound")}) -> ({expected_entry("F","i","a","first")}) -> ({expected_entry("G","j","b","second")}) -> ({E("n*i+j","z","entry")}) -> ({mul("a","b","z","result")})',
        'signed_cartesian_flat_prefix_zero': f'forall F G n T z. ({expected_table("0","T","table")}) -> ({expected_entry("T","0","z","lookup")}) -> ({E("0","z","value")}) -> ({Q("0","T","prefix")})',
        'signed_cartesian_flat_prefix_append': f'forall F G n l T z. ({Q("l","T","before")}) -> ({E("S l","z","next")}) -> exists U. '+conjunction(Q('S l','U','after'),expected_equal('T','U','S l','equal')),
        'signed_cartesian_flat_prefix_exists': f'forall F G n l. ({F0}) -> ({G0}) -> ~(n=0) -> exists T. ({Q("l","T","result")})',
        'signed_cartesian_product_from_flat_prefix': f'forall F G T m n. ({F0}) -> ({G0}) -> ({Q("m*n","T","source")}) -> ({P()})',
        'signed_cartesian_product_empty_columns': f'forall F G T m. ({F0}) -> ({G0}) -> ({expected_table("0","T","T0")}) -> ({P(n="0")})',
        'signed_cartesian_product_exists': f'forall F G m n. ({F0}) -> ({G0}) -> exists T. ({P()})',
        'signed_cartesian_product_row_scalar': f'forall F G T V m n i a. ({P()}) -> ({lt("i","m","row")}) -> ({expected_entry("F","i","a","first")}) -> ({expected_slice("T","V","0+n*i","1","n","slice")}) -> ({expected_scale("a","G","V","n","scalar")})',
        'signed_cartesian_product_row_sum': f'forall F G T m n i a b c. ({P()}) -> ({lt("i","m","row")}) -> ({expected_entry("F","i","a","first")}) -> ({second}) -> ({expected_slice_sum("T","0+n*i","1","n","c","row")}) -> ({result})',
        'signed_cartesian_product_row_sums_scalar': f'forall F G T R m n b. ({P()}) -> ({second}) -> ({expected_rows("T","R","0","n","1","m","n","rows")}) -> ({expected_scale("b","F","R","m","scale")})',
        'signed_cartesian_product_rectangular_sum': f'forall F G T m n a b c. ({P()}) -> ({first}) -> ({second}) -> ({rect}) -> ({result})',
        'signed_cartesian_product_prefix_sum': f'forall F G T m n a b c. ({P()}) -> ({first}) -> ({second}) -> ({prefix}) -> ({result})',
        'signed_cartesian_product_sums_exists': f'forall F G m n. ({F0}) -> ({G0}) -> exists T a b c. '+conjunction(P(),first,second,prefix,result),
        'signed_cartesian_quotient_row_bound': f'forall m n k i j. k=n*i+j -> ({lt("k","m*n","source")}) -> ({lt("i","m","row")})',
        'signed_cartesian_coordinates_exists': f'forall m n k. ({lt("k","m*n","source")}) -> ({expected_coordinates("m","n","k","result")})',
        'signed_cartesian_product_flat_lookup': f'forall F G T m n k z. ({P()}) -> ({lt("k","m*n","source")}) -> ({expected_entry("T","k","z","lookup")}) -> exists d e a b. '+conjunction('k=n*d+e',lt('d','m','row'),lt('e','n','column'),expected_entry('F','d','a','left'),expected_entry('G','e','b','right'),mul('a','b','z','result')),
        'signed_cartesian_product_extensional_unique': f'forall F G T U m n. ({P()}) -> ({P(T="U",tag="other")}) -> ({expected_equal("T","U","m*n","equal")})',
        'signed_cartesian_product_reencode': f'forall F G T U m n. ({P()}) -> ({expected_table("0","U","valid")}) -> ({expected_equal("T","U","m*n","equal")}) -> ({P(T="U",tag="other")})',
        'signed_cartesian_product_exists_extensionally_unique': f'forall F G m n. ({F0}) -> ({G0}) -> exists T. '+conjunction(P(),f'forall U. ({P(T="U",tag="other")}) -> ({expected_equal("T","U","m*n","equal")})'),
    }


EXPECTED=((52,25),(401,40),(83,26),(135,35),(83,27),(70,38),(60,34),(74,28),
          (112,43),(97,57),(92,41),(104,60),(49,28),(72,34),(48,25),(52,22),
          (92,39),(120,37),(114,41),(34,22))


@pytest.mark.parametrize('row',rows(),ids=lambda row:row.name)
def test_original_ha_body(row):
    receipt=checked(row,core() | {item.name:item for item in rows()})
    assert (receipt.proof_nodes,receipt.proof_depth)==EXPECTED[rows().index(row)]
    assert 0<receipt.proof_objects<=receipt.proof_nodes and receipt.proof_depth<=256


@pytest.mark.parametrize('row',rows(),ids=lambda row:row.name)
def test_false_target_is_rejected(row):
    gc.collect()
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


def test_native_order_and_exact_used_dependencies():
    available=set(core())
    assert len(rows())==20
    assert sum(len(row.dependencies) for row in rows())==70
    assert sum(len(row.script) for row in rows())==1081
    for row in rows():
        assert row.name not in available and len(row.dependencies)==len(set(row.dependencies))
        assert set(row.dependencies)<=available
        assert all(re.search(r"(?<![\w'])"+re.escape(name)+r"(?![\w'])",'\n'.join(row.script)) for name in row.dependencies)
        assert not any(command.startswith(('use ','admit','sorry','DNE','ring')) for command in row.script)
        _closed_formula(row.statement)
        available.add(row.name)


@pytest.mark.parametrize('row',rows(),ids=lambda row:row.name)
def test_every_statement_has_an_independent_expanded_contract(row):
    _assert_same_ast(_closed_formula(row.statement),_closed_formula(contracts()[row.name]))


@pytest.mark.parametrize('mode',('identifiers','compound','huge','zero','repeated'))
def test_public_graph_exact_ast_with_full_context(mode):
    context=('F','G','T','m','n')
    arguments=context
    if mode=='compound':arguments=('F+G','G*2','T+1','m+n','n+1')
    if mode=='huge':arguments=('98765432109876543210987654321098765432109876543210',*context[1:])
    if mode=='zero':arguments=('0',)*5
    if mode=='repeated':arguments=('F',)*5
    actual=candidate.signed_cartesian_product_relation(*arguments,tag='contract',variables=context)
    expected=expected_product(*arguments,'independent')
    _assert_same_ast(_closed_formula('forall '+' '.join(context)+'. '+actual),_closed_formula('forall '+' '.join(context)+'. '+expected))


def test_every_generated_binder_is_rejected_even_if_unused_by_arguments():
    context=('F','G','T','m','n')
    source=candidate.signed_cartesian_product_relation(*context,tag='capture',variables=context)
    binders={name for clause in re.findall(r'\b(?:forall|exists)\s+([^.]*)\.',source) for name in clause.split()}
    assert binders and not binders.intersection(context)
    for name in binders:
        with pytest.raises(ValueError):
            candidate.signed_cartesian_product_relation(*context,tag='capture',variables=(*context,name))


@pytest.mark.parametrize('malformed',('unknown','syntax','empty_context','duplicate_context','missing_context','reserved_tag','bad_arity'))
def test_bad_graph_terms_or_contexts_fail_closed(malformed):
    context=('F','G','T','m','n');arguments=context;tag='bad'
    if malformed=='unknown':arguments=('missing',*arguments[1:])
    elif malformed=='syntax':arguments=('F -> G',*arguments[1:])
    elif malformed=='empty_context':context=()
    elif malformed=='duplicate_context':context=(*context,'F')
    elif malformed=='missing_context':context=context[:-1]
    elif malformed=='reserved_tag':tag='forall'
    else:arguments=arguments[:-1]
    with pytest.raises((ValueError,TypeError)):
        candidate.signed_cartesian_product_relation(*arguments,tag=tag,variables=context)


@pytest.mark.parametrize('first,second',(((),()),((),(2,-1)),((2,-1),()),((1,),(1,)),((-1,),(-1,)),((2,-3),(5,-2,1)),((0,3,-4),(-2,5))))
def test_real_beta_outer_products_and_all_actual_sum_traces(first,second):
    m,n=len(first),len(second)
    F=model_table(first,offset=3,endpoint=991);G=model_table(second,offset=7,endpoint=-997)
    values=tuple(a*b for a in first for b in second)
    T=model_table(values,offset=11,endpoint=919);U=model_table(values,offset=17,endpoint=-929)
    assert T[0]!=U[0]
    for i in range(m):
        for j in range(n):
            assert decode_signed(model_at(T,n*i+j))==decode_signed(model_at(F,i))*decode_signed(model_at(G,j))
            assert model_at(T,n*i+j)==model_at(U,n*i+j)
    a=actual_sum_trace(F,m);b=actual_sum_trace(G,n);c=actual_sum_trace(T,m*n)
    assert c==actual_sum_trace(U,m*n)==encode_signed(decode_signed(a)*decode_signed(b))
    assert model_at(T,m*n)!=model_at(U,m*n)
    if not m or not n:assert c==0


def test_signed_codes_and_physical_stride_cannot_be_replaced_by_natural_products():
    assert encode_signed(1)==2 and encode_signed(-1)==1
    assert encode_signed((-1)*(-1))==2!=encode_signed(-1)*encode_signed(-1)
    values=tuple(a*b for a in (2,3) for b in (5,7,11))
    assert values[3*1+0]==15 and values[2*1+0]==22


def test_exact_novelty_against_all3796_prior_and_all_block_rows():
    import constructive_dirichlet_inverse_support as support
    from peano_lab.library import dirichlet_signed_unit_candidate, dirichlet_triangular_candidate, dirichlet_inverse_candidate
    old40=tuple(row for module in (dirichlet_signed_unit_candidate,dirichlet_triangular_candidate,dirichlet_inverse_candidate)
                for row in getattr(module,'make_'+module.__name__.rsplit('.',1)[1].replace('_candidate','')+'_candidate_theorems')(TheoremSpec))
    assert len(old40)==40 and support.PRIOR_THEOREM_COUNT==3756
    assert support.statement_duplicates((*old40,*block_rows(),*rows()))==()
