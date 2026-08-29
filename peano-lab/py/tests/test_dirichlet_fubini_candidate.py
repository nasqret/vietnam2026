"""Independent factor-grid contracts and bounded original-HA regressions.

Numerical cases build actual beta tables and both cumulative traces. These
diagnostics never replace any original-HA certificate or admit a theorem.
"""

from dataclasses import replace
from functools import lru_cache
import gc
from hashlib import sha256
import json
from pathlib import Path
import re
import sys

import pytest

ROOT=Path(__file__).resolve().parents[3]
if str(ROOT/'scripts') not in sys.path:sys.path.insert(0,str(ROOT/'scripts'))
from peano_lab.library import dirichlet_fubini_candidate as candidate
from peano_lab.library.candidate_validation import CandidateBodyError,replay_candidate_bodies
from peano_lab.library.theorems import TheoremSpec,_closed_formula
from peano_lab.library import campaign_bottom_layer_closure as closure
from constructive_dirichlet_support import previous_rows,statement_duplicates
from tests.test_divisor_sum_table_candidate import _assert_same_ast
from tests.test_dirichlet_convolution_candidate import (
    _conjoin,expected_at,expected_table,expected_signed_sum,expected_signed_multiply,
    expected_le,expected_dvd,expected_entry as expected_convolution_entry,
    expected_prefix as expected_convolution_prefix,expected_convolution,
    expected_convolution_table,expected_equal,
)
from tests.test_signed_rectangular_slice_candidate import (
    _instantiate,expected_slice,actual_sum_trace,BoundedTestSelection,
)
from tests.test_signed_rectangular_sums_candidate import expected_rows,expected_fubini_witnesses
from tests.test_signed_table_operations_candidate import (
    expected_scalar as old_expected_scalar,model_table,model_at,encode_signed,decode_signed,
)


EXPECTED=((11,10),(41,34),(91,44),(308,43),(123,39),(135,47),(142,41),(44,24),
          (337,40),(114,28),(156,36),(88,29),(67,29),(31,19),(39,26),(35,23),
          (166,46),(91,39),(61,39),(103,45),(81,36),(116,39),(40,19),(97,57),
          (113,47),(214,52),(92,42),(92,42),(145,45))
ROOT_PINS={
    'dirichlet_grid_table_exists':'ef386d6ac10cfafeeb56893d3efa02aa4fa4e6ca6a7a2988d5a571c43508ad9c',
    'dirichlet_grid_fubini_exists':'84c13a3b8852328db17b1b2a3b7b6bf8939a9b5c62a1dccbabf9fbe2a6892675',
    'dirichlet_convolution_fubini_interchange':'52ec70863e39714463cce993fd232ffe99a1a5e0c5a97f0daecfe5b41ed8e3bd',
}


@lru_cache(maxsize=1)
def rows():return candidate.make_dirichlet_fubini_candidate_theorems(TheoremSpec)


@lru_cache(maxsize=1)
def core():
    from peano_lab.library.dirichlet_convolution_candidate import make_dirichlet_convolution_candidate_theorems
    from peano_lab.library.signed_finite_support_candidate import make_signed_finite_support_candidate_theorems
    from peano_lab.library.dirichlet_commutativity_candidate import make_dirichlet_commutativity_candidate_theorems
    inherited=(*closure.parent_snapshot().specs,*previous_rows())
    assert len(inherited)==len({row.name for row in inherited})==3643
    assert closure.PARENT_CATALOG_SHA256=='ac7111ec14ff07bf899238ed465de337e6d76e9343384947022360dc7e65d9f7'
    return {row.name:row for row in (*inherited,*make_dirichlet_convolution_candidate_theorems(TheoremSpec),
        *make_signed_finite_support_candidate_theorems(TheoremSpec),*make_dirichlet_commutativity_candidate_theorems(TheoremSpec))}


def expected_lt(a,b,tag):
    gap='model_strict_gap_'+tag
    return f'exists {gap}. {gap}+S ({a})=({b})'


def expected_triple(u,v,w,z,tag):
    inner='model_inner_product_'+tag
    return f'exists {inner}. '+_conjoin(expected_signed_multiply(v,w,inner,tag+'inner'),expected_signed_multiply(u,inner,z,tag+'outer'))


def expected_omitted(n,a,e,tag):
    return f'({a})=0 \\/ (({e})=0 \\/ ~({expected_dvd(f"({a})*({e})",n,tag+"nondivisor")}))'


def expected_grid_entry(F,G,H,n,a,e,z,tag):
    c,u,v,w=('model_grid_'+role+'_'+tag for role in ('middle','first','last','value'))
    retained=_conjoin(f'~(({a})=0)',f'~(({e})=0)',f'exists {c} {u} {v} {w}. '+_conjoin(
        f'({n})=(({a})*({e}))*{c}',expected_at(F,a,u,tag+'first'),expected_at(H,e,v,tag+'last'),
        expected_at(G,c,w,tag+'middle'),expected_triple(u,v,w,z,tag+'products')))
    omitted=_conjoin(expected_omitted(n,a,e,tag+'omitted'),f'({z})=0')
    return f'({retained}) \\/ ({omitted})'


def expected_index(n,a,e):return f'(S ({n}))*({a})+({e})'


def expected_flat_entry(F,G,H,n,i,z,tag):
    a,e='model_flat_row_'+tag,'model_flat_column_'+tag
    return f'exists {a} {e}. '+_conjoin(f'({i})=({expected_index(n,a,e)})',expected_lt(e,f'S ({n})',tag+'remainder'),expected_grid_entry(F,G,H,n,a,e,z,tag+'cell'))


def expected_flat_prefix(F,G,H,n,l,T,tag):
    i,z='model_prefix_index_'+tag,'model_prefix_value_'+tag
    return _conjoin(expected_table(l,T,tag+'table'),f'forall {i} {z}. ({expected_le(i,l,tag+"bound")}) -> '
        f'({expected_at(T,i,z,tag+"lookup")}) -> ({expected_flat_entry(F,G,H,n,i,z,tag+"entry")})')


def expected_grid(F,G,H,n,T,tag):
    a,e,z=('model_square_'+role+'_'+tag for role in ('row','column','value'))
    return _conjoin(expected_table(f'(S ({n}))*(S ({n}))',T,tag+'table'),
        f'forall {a} {e} {z}. ({expected_le(a,n,tag+"row")}) -> ({expected_le(e,n,tag+"column")}) -> '
        f'({expected_at(T,expected_index(n,a,e),z,tag+"lookup")}) -> ({expected_grid_entry(F,G,H,n,a,e,z,tag+"cell")})')


def expected_factor_row(F,G,H,n,a,V,tag):
    e,z='model_factor_column_'+tag,'model_factor_value_'+tag
    return _conjoin(expected_table(f'S ({n})',V,tag+'table'),f'forall {e} {z}. ({expected_le(e,n,tag+"bound")}) -> '
        f'({expected_at(V,e,z,tag+"lookup")}) -> ({expected_grid_entry(F,G,H,n,a,e,z,tag+"cell")})')


def expected_scalar(a,F,G,l,tag):
    return _instantiate(old_expected_scalar('SCALAR','INPUT','OUTPUT','LENGTH'),{'SCALAR':a,'INPUT':F,'OUTPUT':G,'LENGTH':l},tag)


def expected_statements():
    """All 29 targets, independently assembled without factory formulas."""
    counter=0
    def tagged(function):
        def call(*args):
            nonlocal counter
            counter+=1
            return function(*args,tag='statement_'+str(counter))
        return call
    (T,A,M,S,L,D,LT,E,O,TR,FE,FP,GR,FR,SC,EQ,CE,CP,C,CT,SL,RS,FB)=tuple(tagged(function) for function in (
        expected_table,expected_at,expected_signed_multiply,expected_signed_sum,expected_le,expected_dvd,
        expected_lt,expected_grid_entry,expected_omitted,expected_triple,expected_flat_entry,expected_flat_prefix,
        expected_grid,expected_factor_row,expected_scalar,expected_equal,expected_convolution_entry,
        expected_convolution_prefix,expected_convolution,expected_convolution_table,expected_slice,expected_rows,expected_fubini_witnesses))
    def all_(names,*clauses):return 'forall '+names+'. '+' -> '.join('('+clause+')' for clause in clauses)
    def exists(names,*clauses):return 'exists '+names+'. '+_conjoin(*clauses)
    nz=lambda value:f'~(({value})=0)'
    zero_row=lambda:f'a=0 \\/ ~({D("a","n")})'
    return {
        'dirichlet_grid_entry_omitted':all_('F G H n a e',O('n','a','e'),E('F','G','H','n','a','e','0')),
        'dirichlet_grid_entry_from_factorization':all_('F G H n a e c u v w r z',nz('a'),nz('e'),'n=(a*e)*c',A('F','a','u'),A('H','e','v'),A('G','c','w'),M('v','w','r'),M('u','r','z'),E('F','G','H','n','a','e','z')),
        'dirichlet_grid_entry_omitted_value':all_('F G H n a e z',O('n','a','e'),E('F','G','H','n','a','e','z'),'z=0'),
        'dirichlet_grid_entry_factor_product':all_('F G H n a e c u v w z',nz('a'),nz('e'),'n=(a*e)*c',A('F','a','u'),A('H','e','v'),A('G','c','w'),E('F','G','H','n','a','e','z'),TR('u','v','w','z')),
        'dirichlet_grid_entry_functional':all_('F G H n a e z Z',E('F','G','H','n','a','e','z'),E('F','G','H','n','a','e','Z'),'z=Z'),
        'dirichlet_grid_entry_exists':all_('F G H n a e',T('0','F'),T('0','G'),T('0','H'),exists('z',E('F','G','H','n','a','e','z'))),
        'dirichlet_grid_entry_transpose':all_('F G H n a e z',E('F','G','H','n','a','e','z'),E('H','G','F','n','e','a','z')),
        'dirichlet_grid_flat_entry_exists':all_('F G H n i',T('0','F'),T('0','G'),T('0','H'),exists('z',FE('F','G','H','n','i','z'))),
        'dirichlet_grid_flat_entry_coordinates':all_('F G H n a e z',LT('e','S n'),FE('F','G','H','n',expected_index('n','a','e'),'z'),E('F','G','H','n','a','e','z')),
        'dirichlet_grid_flat_prefix_zero':all_('F G H n T z',T('0','T'),A('T','0','z'),FE('F','G','H','n','0','z'),FP('F','G','H','n','0','T')),
        'dirichlet_grid_flat_prefix_append':all_('F G H n l T z',FP('F','G','H','n','l','T'),FE('F','G','H','n','S l','z'),exists('U',FP('F','G','H','n','S l','U'),EQ('T','U','S l'))),
        'dirichlet_grid_flat_prefix_exists':all_('F G H n l',T('0','F'),T('0','G'),T('0','H'),exists('T',FP('F','G','H','n','l','T'))),
        'dirichlet_grid_from_flat_prefix':all_('F G H n T',FP('F','G','H','n','(S n)*(S n)','T'),GR('F','G','H','n','T')),
        'dirichlet_grid_table_exists':all_('F G H n',T('0','F'),T('0','G'),T('0','H'),exists('T',GR('F','G','H','n','T'))),
        'dirichlet_grid_table_lookup':all_('F G H n T a e z',GR('F','G','H','n','T'),L('a','n'),L('e','n'),A('T',expected_index('n','a','e'),'z'),E('F','G','H','n','a','e','z')),
        'dirichlet_grid_middle_factor_equation':all_('n a e c q',nz('a'),'n=a*q','n=(a*e)*c','q=e*c'),
        'dirichlet_grid_entry_from_convolution_entry':all_('F G H n a q u e v z',nz('a'),'n=a*q',A('F','a','u'),CE('H','G','q','e','v'),M('u','v','z'),E('F','G','H','n','a','e','z')),
        'dirichlet_grid_entry_convolution_product':all_('F G H n a q u e v z',nz('a'),'n=a*q',A('F','a','u'),CE('H','G','q','e','v'),E('F','G','H','n','a','e','z'),M('u','v','z')),
        'dirichlet_grid_nondivisor_row_value_zero':all_('F G H n a e z',zero_row(),E('F','G','H','n','a','e','z'),'z=0'),
        'dirichlet_factor_row_scalar':all_('F G H n a q u V P',nz('a'),'n=a*q',A('F','a','u'),CP('H','G','q','n','P'),FR('F','G','H','n','a','V'),SC('u','P','V','S n')),
        'dirichlet_grid_row_slice':all_('F G H n T a V',GR('F','G','H','n','T'),L('a','n'),SL('T','V','0+(S n)*a','1','S n'),FR('F','G','H','n','a','V')),
        'dirichlet_grid_column_slice':all_('F G H n T a V',GR('F','G','H','n','T'),L('a','n'),SL('T','V','0+1*a','S n','S n'),FR('H','G','F','n','a','V')),
        'dirichlet_grid_fubini_exists':all_('F G H n',T('0','F'),T('0','G'),T('0','H'),exists('T R C z',GR('F','G','H','n','T'),FB('T','R','C','0','S n','1','S n','S n','z'))),
        'dirichlet_factor_row_zero_sum':all_('F G H n a V z',FR('F','G','H','n','a','V'),zero_row(),S('V','S n','z'),'z=0'),
        'dirichlet_factor_row_sum_product':all_('F G H n a q u V z',T('0','H'),T('0','G'),nz('n'),nz('a'),'n=a*q',A('F','a','u'),FR('F','G','H','n','a','V'),S('V','S n','z'),exists('v',C('H','G','q','v'),M('u','v','z'))),
        'dirichlet_factor_row_nested_entry':all_('N F G H U n a V z',T('N','F'),CT('N','H','G','U'),nz('n'),L('n','N'),L('a','n'),FR('F','G','H','n','a','V'),S('V','S n','z'),CE('F','U','n','a','z')),
        'dirichlet_grid_row_sums_convolution_prefix':all_('N F G H U n T R',T('N','F'),CT('N','H','G','U'),nz('n'),L('n','N'),GR('F','G','H','n','T'),RS('T','R','0','S n','1','S n','S n'),CP('F','U','n','n','R')),
        'dirichlet_grid_column_sums_convolution_prefix':all_('N F G H U n T R',T('N','H'),CT('N','F','G','U'),nz('n'),L('n','N'),GR('F','G','H','n','T'),RS('T','R','0','1','S n','S n','S n'),CP('H','U','n','n','R')),
        'dirichlet_convolution_fubini_interchange':all_('N F G H U V n a b',CT('N','H','G','U'),CT('N','F','G','V'),nz('n'),L('n','N'),C('F','U','n','a'),C('H','V','n','b'),'a=b'),
    }


SURFACES=(
    (candidate.signed_dirichlet_grid_entry_relation,expected_grid_entry,('F','G','H','n','a','e','z')),
    (candidate.signed_dirichlet_grid_table_relation,expected_grid,('F','G','H','n','T')),
    (candidate.signed_dirichlet_flat_entry_relation,expected_flat_entry,('F','G','H','n','i','z')),
    (candidate.signed_dirichlet_flat_prefix_relation,expected_flat_prefix,('F','G','H','n','l','T')),
    (candidate.signed_dirichlet_factor_row_relation,expected_factor_row,('F','G','H','n','a','V')),
)


@pytest.mark.parametrize('builder,model,arguments',SURFACES)
@pytest.mark.parametrize('mode',('identifiers','compound','large','zero','repeated'))
def test_independent_exact_public_graphs(builder,model,arguments,mode):
    context=('F','G','H','n','a','e','z','T','i','l','V','unused')
    if mode=='compound':arguments=tuple(f'({arg})+n' if i%2==0 else f'({arg})*F' for i,arg in enumerate(arguments))
    if mode=='large':arguments=('79228162514264337593543950335',*arguments[1:])
    if mode=='zero':arguments=('0',)*len(arguments)
    if mode=='repeated':arguments=('F',)*len(arguments)
    close='forall '+' '.join(context)+'. '
    _assert_same_ast(_closed_formula(close+builder(*arguments,tag='contract',variables=context)),
                     _closed_formula(close+model(*arguments,tag='independent')))


@pytest.mark.parametrize('builder,model,arguments',SURFACES)
def test_every_generated_binder_rejects_whole_context_capture(builder,model,arguments):
    context=tuple(dict.fromkeys((*arguments,'unused')))
    source=builder(*arguments,tag='capture',variables=context)
    binders={name for clause in re.findall(r'\b(?:forall|exists)\s+([^.]*)\.',source) for name in clause.split()}
    assert binders and not binders.intersection(context)
    for binder in binders:
        with pytest.raises(ValueError):builder(*arguments,tag='capture',variables=context+(binder,))


@pytest.mark.parametrize('builder,model,arguments',SURFACES)
@pytest.mark.parametrize('bad',('unknown','formula','division','empty','duplicate','missing','list','bad-tag','reserved-tag'))
def test_invalid_terms_contexts_and_tags_fail_closed(builder,model,arguments,bad):
    context=tuple(dict.fromkeys(arguments));tag='invalid'
    if bad=='unknown':arguments=('unknown_variable',*arguments[1:])
    if bad=='formula':arguments=('F -> false',*arguments[1:])
    if bad=='division':arguments=('F / 2',*arguments[1:])
    if bad=='empty':context=()
    if bad=='duplicate':context=context+(context[0],)
    if bad=='missing':context=context[:-1]
    if bad=='list':context=list(context)
    if bad=='bad-tag':tag='bad tag'
    if bad=='reserved-tag':tag='forall'
    with pytest.raises(ValueError):builder(*arguments,tag=tag,variables=context)


@pytest.mark.parametrize('row',rows(),ids=lambda row:row.name)
def test_every_theorem_has_an_independent_exact_contract(row):
    statements=expected_statements()
    assert tuple(statements)==tuple(item.name for item in rows())
    _assert_same_ast(_closed_formula(row.statement),_closed_formula(statements[row.name]))


def test_exact_topology_actual_dependencies_and_pinned_inventory():
    assert len(rows())==29
    assert sum(len(row.dependencies) for row in rows())==111
    assert sum(len(row.script) for row in rows())==1790
    assert sha256('\n'.join(row.name for row in rows()).encode()).hexdigest()=='9e73be88ffa3bd8b307603845ffb37b44843b10b42eaa0b4af16b36bc0ae43e2'
    available=set(core())
    for row in rows():
        assert row.name not in available
        assert len(row.dependencies)==len(set(row.dependencies))
        assert set(row.dependencies)<=available
        assert all(re.search(r'(?<![\w\'])'+re.escape(dep)+r'(?![\w\'])','\n'.join(row.script)) for dep in row.dependencies)
        assert not any(command.startswith(('use ','admit','sorry','DNE','ring')) for command in row.script)
        available.add(row.name)
    assert {row.name:sha256(row.statement.encode()).hexdigest() for row in rows() if row.name in ROOT_PINS}==ROOT_PINS


def test_exact_ast_novelty_against_all_3643_prior_rows():
    assert statement_duplicates(rows())==()


@pytest.mark.parametrize('row',rows(),ids=lambda row:row.name)
def test_original_kernel_body(row):
    try:
        receipt=replay_candidate_bodies((row,),core=core()|{item.name:item for item in rows()})[0]
        assert (receipt.proof_nodes,receipt.proof_depth)==EXPECTED[rows().index(row)]
        assert receipt.proof_objects==receipt.proof_nodes-(7 if row.name=='dirichlet_grid_entry_factor_product' else 0)
    except CandidateBodyError as error:pytest.fail(str(error),pytrace=False)
    finally:gc.collect()


@pytest.mark.parametrize('row',rows(),ids=lambda row:row.name)
def test_false_target_cannot_reuse_the_body(row):
    with pytest.raises(CandidateBodyError):replay_candidate_bodies((replace(row,statement='0=1'),),core=core()|{item.name:item for item in rows()})


@pytest.mark.parametrize('row',rows(),ids=lambda row:row.name)
def test_missing_actual_body_is_rejected(row):
    with pytest.raises(CandidateBodyError):replay_candidate_bodies((replace(row,script=()),),core=core()|{item.name:item for item in rows()})


DEPENDENCIES=tuple((row,dependency) for row in rows() for dependency in row.dependencies)


@pytest.mark.parametrize('row,dependency',DEPENDENCIES,ids=lambda value:value.name if hasattr(value,'name') else value)
def test_dropped_dependency_cannot_be_used(row,dependency):
    changed=replace(row,dependencies=tuple(name for name in row.dependencies if name!=dependency))
    with pytest.raises(CandidateBodyError):replay_candidate_bodies((changed,),core=core()|{item.name:item for item in rows()})


@pytest.mark.parametrize('row,dependency',DEPENDENCIES,ids=lambda value:value.name if hasattr(value,'name') else value)
def test_poisoned_dependency_cannot_replace_its_actual_statement(row,dependency):
    table=core()|{item.name:item for item in rows()}
    table[dependency]=replace(table[dependency],statement='0=1')
    with pytest.raises(CandidateBodyError):replay_candidate_bodies((row,),core=table)


def actual_convolution(F,G,n,*,offset=7):
    """Diagnostic actual mask AND cumulative beta traces, only for n>0."""
    if n<=0:raise ValueError('a convolution input is positive')
    values=tuple(0 if d==0 or n%d else decode_signed(model_at(F,d))*decode_signed(model_at(G,n//d)) for d in range(n+1))
    mask=model_table(values,offset=offset,endpoint=-919)
    assert all(model_at(mask,d)==encode_signed(value) for d,value in enumerate(values))
    result=actual_sum_trace(mask,n+1)
    assert result==encode_signed(sum(values))
    return result,mask


def actual_factor_grid(F,G,H,n,*,offset=5,endpoint=991):
    side=n+1;values=[]
    for i in range(side*side):
        a,e=divmod(i,side)
        assert i==side*a+e and 0<=e<side and 0<=a<side
        if a==0 or e==0 or n%(a*e):value=0
        else:
            c=n//(a*e)
            assert n==(a*e)*c
            if n:assert 0<c<=n
            value=decode_signed(model_at(F,a))*(decode_signed(model_at(H,e))*decode_signed(model_at(G,c)))
        values.append(value)
    table=model_table(tuple(values),offset=offset,endpoint=endpoint)
    assert all(model_at(table,i)==encode_signed(value) for i,value in enumerate(values))
    return table,tuple(values)


@pytest.mark.parametrize('n',(0,1,2,4,6))
@pytest.mark.parametrize('zeros',((0,0,0),(17,-19,23)))
def test_actual_beta_factor_grid_row_column_traces_and_nested_convolutions(n,zeros):
    values=(tuple([zeros[0]]+[(-1)**i*(i+1) for i in range(1,n+1)]),
            tuple([zeros[1]]+[2-i for i in range(1,n+1)]),tuple([zeros[2]]+[(-1)**(i+1)*(i+2) for i in range(1,n+1)]))
    F,G,H=tuple(model_table(data,offset=index+2,endpoint=811+index) for index,data in enumerate(values))
    T,cells=actual_factor_grid(F,G,H,n);other,_=actual_factor_grid(F,G,H,n,offset=13,endpoint=-991)
    side=n+1
    assert T[0]!=other[0] and T[1]!=other[1]
    assert model_at(T,side*side)!=model_at(other,side*side)
    row_values=[];column_values=[]
    for a in range(side):
        row=model_table(tuple(cells[side*a+e] for e in range(side)),offset=11,endpoint=887)
        column=model_table(tuple(cells[side*e+a] for e in range(side)),offset=17,endpoint=-887)
        for e in range(side):
            assert model_at(row,e)==model_at(T,side*a+e)==model_at(other,side*a+e)
            assert model_at(column,e)==model_at(T,side*e+a)
        row_value=decode_signed(actual_sum_trace(row,side));column_value=decode_signed(actual_sum_trace(column,side))
        row_values.append(row_value);column_values.append(column_value)
        if n and a and n%a==0:
            q=n//a
            assert 0<q<=n
            inner_row,_=actual_convolution(H,G,q);inner_column,_=actual_convolution(F,G,q)
            assert row_value==decode_signed(model_at(F,a))*decode_signed(inner_row)
            assert column_value==decode_signed(model_at(H,a))*decode_signed(inner_column)
        else:assert row_value==column_value==0
    R=model_table(tuple(row_values),offset=19,endpoint=881);C=model_table(tuple(column_values),offset=23,endpoint=-881)
    assert actual_sum_trace(R,side)==actual_sum_trace(C,side)==encode_signed(sum(cells))
    if n==0:assert cells==(0,) and actual_sum_trace(R,side)==0


@pytest.mark.parametrize('n',(1,2,4,6))
def test_real_inner_prefix_zero_padding_and_excluded_zero_values(n):
    F=model_table(tuple([97]+[i+1 for i in range(1,n+1)]),offset=3)
    G=model_table(tuple([-101]+[2-i for i in range(1,n+1)]),offset=5)
    for q in range(1,n+1):
        canonical,_=actual_convolution(F,G,q)
        padded=tuple(0 if d==0 or q%d else decode_signed(model_at(F,d))*decode_signed(model_at(G,q//d)) for d in range(n+1))
        table=model_table(padded,offset=11,endpoint=797)
        assert all(padded[d]==0 for d in range(q+1,n+1))
        assert actual_sum_trace(table,q+1)==actual_sum_trace(table,n+1)==canonical


def test_zero_input_grid_is_not_a_convolution_at_zero_and_flat_remainder_is_strict():
    F=model_table((7,11),offset=2);G=model_table((13,17),offset=3);H=model_table((19,23),offset=5)
    T,cells=actual_factor_grid(F,G,H,0)
    assert cells==(0,) and actual_sum_trace(T,1)==0
    with pytest.raises(ValueError):actual_convolution(F,G,0)
    assert 3*0+3==3*1+0 and (0,3)!=(1,0)
    assert 0==(0*1)*0==(0*1)*1
    assert 7*(23*13)!=7*(23*17)


if __name__=='__main__':
    import argparse,resource,signal,time
    parser=argparse.ArgumentParser();parser.add_argument('--body');parser.add_argument('--start',type=int,default=0);parser.add_argument('--count',type=int,default=1);parser.add_argument('--pytest-select');parser.add_argument('--case-start',type=int,default=0);parser.add_argument('--case-count',type=int)
    args=parser.parse_args();resource.setrlimit(resource.RLIMIT_CPU,(170,175));signal.alarm(180);started=time.monotonic()
    if args.pytest_select is not None:
        plugins=[] if args.case_count is None else [BoundedTestSelection(args.case_start,args.case_count)]
        status=pytest.main(['-q',__file__,'-k',args.pytest_select],plugins=plugins)
    else:
        selected=tuple(row for row in rows() if row.name==args.body) if args.body else rows()[args.start:args.start+args.count]
        if not selected:raise SystemExit('unknown theorem body')
        for row in selected:
            test_original_kernel_body(row)
            print(json.dumps({'name':row.name,'nodes':EXPECTED[rows().index(row)][0],'depth':EXPECTED[rows().index(row)][1]}),flush=True)
        status=0
    peak=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss*(1 if sys.platform=='darwin' else 1024)
    assert peak<=1536*1024*1024
    print(json.dumps({'status':status,'seconds':time.monotonic()-started,'peak_rss_bytes':peak}),flush=True)
    raise SystemExit(status)
