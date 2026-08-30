"""Independent graph/target contracts, genuine HA bodies, and actual beta models.

Numerical CRT tables and finite traces are diagnostics, never proof evidence.
Original-kernel checks here leave exact declared dependencies as hypotheses;
complete closure and admission are separate, unclaimed gates.
"""

from __future__ import annotations

from dataclasses import replace
from functools import lru_cache
import gc
from hashlib import sha256
import random
import re

import pytest

from peano_lab.library import signed_support_reindex_candidate as candidate
from peano_lab.kernel.formulas import parse_formula_in_context
from peano_lab.library.candidate_validation import CandidateBodyError, replay_candidate_bodies
from peano_lab.library.formula_dag import FormulaArena
from peano_lab.library.theorems import _closed_formula
from tests.test_divisor_sum_table_candidate import _assert_same_ast
from tests.test_signed_rectangular_slice_candidate import (
    actual_sum_trace, expected_entry as expected_at, expected_slice,
    expected_slice_sum, expected_sum, expected_table,
)
from tests.test_signed_rectangular_sums_candidate import expected_rows
from tests.test_signed_table_operations_candidate import (
    beta_stream, decode_signed, encode_signed, model_at, model_table,
)


@lru_cache(maxsize=1)
def core():
    from tests.test_signed_rectangular_sums_candidate import core as previous_core, rows as rectangle_rows
    from peano_lab.library.signed_finite_support_candidate import make_signed_finite_support_candidate_theorems
    from peano_lab.library.theorems import TheoremSpec
    result = previous_core() | {row.name:row for row in rectangle_rows()}
    result.update((row.name,row) for row in make_signed_finite_support_candidate_theorems(TheoremSpec))
    return result


@lru_cache(maxsize=1)
def rows():
    from peano_lab.library.theorems import TheoremSpec
    from peano_lab.library.signed_support_reindex_candidate import make_signed_support_reindex_candidate_theorems
    return make_signed_support_reindex_candidate_theorems(TheoremSpec)


METRICS=(
    (48,48,27),(57,57,26),(124,124,48),(18,18,15),(20,20,17),
    (57,57,25),(80,80,26),(60,60,26),(32,32,20),(65,65,28),
    (37,37,19),(177,177,32),(84,84,27),(136,136,36),(72,72,27),
    (68,68,33),(29,29,19),(83,83,34),(92,92,35),(278,278,53),
    (544,544,64),(56,56,36),(56,56,36),(111,111,38),(64,64,28),
)


def conjunction(*clauses):
    return clauses[0] if len(clauses)==1 else f'(({clauses[0]}) /\\ ({conjunction(*clauses[1:])}))'


def expected_lt(a,b,tag):
    gap='independent_lt_'+tag
    return f'exists {gap}. {gap}+S ({a})=({b})'


def expected_le(a,b,tag):
    gap='independent_le_'+tag
    return f'exists {gap}. {gap}+({a})=({b})'


def expected_beta(r,s,i,j,tag):
    gap,quotient='independent_beta_gap_'+tag,'independent_beta_quotient_'+tag
    modulus=f'S ((S ({i}))*({s}))'
    return conjunction(f'exists {gap}. {gap}+S ({j})={modulus}',
                       f'exists {quotient}. ({r})={quotient}*{modulus}+({j})')


def expected_zero_window(F,k,l,tag):
    i,z='independent_zero_index_'+tag,'independent_zero_value_'+tag
    return (f'forall {i} {z}. ({expected_le(k,i,tag+"lower")}) -> '
            f'({expected_lt(i,l,tag+"upper")}) -> ({expected_at(F,i,z,tag+"lookup")}) -> {z}=0')


def expected_off_spike(F,l,p,tag):
    i,z='independent_off_index_'+tag,'independent_off_value_'+tag
    return (f'forall {i} {z}. ({expected_lt(i,l,tag+"bound")}) -> ~({i}=({p})) -> '
            f'({expected_at(F,i,z,tag+"lookup")}) -> {z}=0')


def expected_support(A,B,r,s,L,M,tag):
    i,a,j=('independent_preserve_'+name+'_'+tag for name in ('i','a','j'))
    preserve=(f'forall {i} {a}. ({expected_lt(i,L,tag+"source_bound")}) -> '
        f'({expected_at(A,i,a,tag+"source_value")}) -> ~({a}=0) -> exists {j}. '
        +conjunction(expected_beta(r,s,i,j,tag+'image'),expected_lt(j,M,tag+'image_bound'),
                     expected_at(B,j,a,tag+'preserved_value')))
    i,k,j,a,b=('independent_injective_'+name+'_'+tag for name in ('i','k','j','a','b'))
    injective=(f'forall {i} {k} {j} {a} {b}. ({expected_lt(i,L,tag+"first_bound")}) -> '
        f'({expected_lt(k,L,tag+"second_bound")}) -> ({expected_at(A,i,a,tag+"first_value")}) -> ~({a}=0) -> '
        f'({expected_at(A,k,b,tag+"second_value")}) -> ~({b}=0) -> '
        f'({expected_beta(r,s,i,j,tag+"first_map")}) -> ({expected_beta(r,s,k,j,tag+"second_map")}) -> {i}={k}')
    j,b,i=('independent_cover_'+name+'_'+tag for name in ('j','b','i'))
    cover=(f'forall {j} {b}. ({expected_lt(j,M,tag+"target_bound")}) -> '
        f'({expected_at(B,j,b,tag+"target_value")}) -> ~({b}=0) -> exists {i}. '
        +conjunction(expected_lt(i,L,tag+'preimage_bound'),expected_beta(r,s,i,j,tag+'preimage_map'),
                     expected_at(A,i,b,tag+'preimage_value')))
    return conjunction(expected_table('0',A,tag+'valid_source'),expected_table('0',B,tag+'valid_target'),
                       preserve,injective,cover)


def expected_choice(j,k,z,a):
    return f'({conjunction(f"({j})=({k})",f"({z})=({a})")}) \\/ ({conjunction(f"~(({j})=({k}))",f"({z})=0")})'


def expected_incidence_entry(A,r,s,i,j,z,tag):
    a,k='independent_cell_value_'+tag,'independent_cell_image_'+tag
    return f'exists {a} {k}. '+conjunction(expected_at(A,i,a,tag+'source'),
        expected_beta(r,s,i,k,tag+'map'),expected_choice(j,k,z,a))


def expected_index(M,i,j):
    return f'(S ({M}))*({i})+({j})'


def expected_flat_entry(A,r,s,M,k,z,tag):
    i,j='independent_flat_row_'+tag,'independent_flat_column_'+tag
    return f'exists {i} {j}. '+conjunction(f'({k})=({expected_index(M,i,j)})',
        expected_lt(j,f'S ({M})',tag+'remainder'),expected_incidence_entry(A,r,s,i,j,z,tag+'cell'))


def expected_flat_prefix(A,r,s,M,l,T,tag):
    k,z='independent_prefix_index_'+tag,'independent_prefix_value_'+tag
    return conjunction(expected_table(l,T,tag+'valid'),
        f'forall {k} {z}. ({expected_le(k,l,tag+"bound")}) -> ({expected_at(T,k,z,tag+"entry")}) -> '
        f'({expected_flat_entry(A,r,s,M,k,z,tag+"cell")})')


def expected_incidence(A,r,s,L,M,T,tag):
    i,j,z=('independent_grid_'+name+'_'+tag for name in ('row','column','value'))
    return conjunction(expected_table('0',A,tag+'source'),expected_table(f'({L})*(S ({M}))',T,tag+'valid'),
        f'forall {i} {j} {z}. ({expected_lt(i,L,tag+"row_bound")}) -> ({expected_lt(j,M,tag+"column_bound")}) -> '
        f'({expected_at(T,expected_index(M,i,j),z,tag+"value")}) -> ({expected_incidence_entry(A,r,s,i,j,z,tag+"cell")})')


def expected_equal(A,B,l,tag):
    i,a,b=('independent_equal_'+name+'_'+tag for name in ('i','a','b'))
    return (f'forall {i} {a} {b}. ({expected_lt(i,l,tag+"bound")}) -> '
            f'({expected_at(A,i,a,tag+"first")}) -> ({expected_at(B,i,b,tag+"second")}) -> {a}={b}')


@lru_cache(maxsize=1)
def expected_statements():
    counter=0
    def tagged(function):
        def call(*args):
            nonlocal counter
            counter+=1
            return function(*args,tag='statement_'+str(counter))
        return call
    T,A,S,B,LT,LE,Z,O,R,E,F,P,I,Q,SL,SS,RS=map(tagged,(
        expected_table,expected_at,expected_sum,expected_beta,expected_lt,expected_le,
        expected_zero_window,expected_off_spike,expected_support,expected_incidence_entry,
        expected_flat_entry,expected_flat_prefix,expected_incidence,expected_equal,
        expected_slice,expected_slice_sum,expected_rows))
    def all_(variables,*clauses):
        return 'forall '+variables+'. '+' -> '.join('('+part+')' for part in clauses)
    def exists(variables,*clauses):
        return 'exists '+variables+'. '+conjunction(*clauses)
    support=lambda:R('A','B','r','s','L','M')
    incidence=lambda:I('A','r','s','L','M','T')
    row_origin='0+(S M)*i'
    column_origin='0+1*j'
    return {
        'signed_prefix_sum_single_spike_value':all_('F l p a z',T('0','F'),LT('p','l'),Z('F','0','p'),A('F','p','a'),Z('F','S p','l'),S('F','l','z'),'z=a'),
        'signed_prefix_sum_single_spike_exists':all_('F l p a',T('0','F'),LT('p','l'),Z('F','0','p'),A('F','p','a'),Z('F','S p','l'),S('F','l','a')),
        'signed_prefix_sum_point_spike_value':all_('F l p a z',T('0','F'),LT('p','l'),A('F','p','a'),O('F','l','p'),S('F','l','z'),'z=a'),
        'signed_support_incidence_entry_hit':all_('A r s i j a',A('A','i','a'),B('r','s','i','j'),E('A','r','s','i','j','a')),
        'signed_support_incidence_entry_miss':all_('A r s i j k a',A('A','i','a'),B('r','s','i','k'),'~(j=k)',E('A','r','s','i','j','0')),
        'signed_support_incidence_entry_decode':all_('A r s i j a k z',A('A','i','a'),B('r','s','i','k'),E('A','r','s','i','j','z'),expected_choice('j','k','z','a')),
        'signed_support_incidence_entry_functional':all_('A r s i j z w',E('A','r','s','i','j','z'),E('A','r','s','i','j','w'),'z=w'),
        'signed_support_incidence_entry_exists':all_('A r s i j',T('0','A'),exists('z',E('A','r','s','i','j','z'))),
        'signed_support_incidence_zero_source_value':all_('A r s i j z',A('A','i','0'),E('A','r','s','i','j','z'),'z=0'),
        'signed_support_incidence_nonzero_source_image':all_('A r s i j z',E('A','r','s','i','j','z'),'~(z=0)',conjunction(A('A','i','z'),B('r','s','i','j'))),
        'signed_support_incidence_flat_entry_exists':all_('A r s M k',T('0','A'),exists('z',F('A','r','s','M','k','z'))),
        'signed_support_incidence_flat_entry_coordinates':all_('A r s M i j z',LT('j','S M'),F('A','r','s','M',expected_index('M','i','j'),'z'),E('A','r','s','i','j','z')),
        'signed_support_incidence_flat_prefix_zero':all_('A r s M T z',T('0','T'),A('T','0','z'),F('A','r','s','M','0','z'),P('A','r','s','M','0','T')),
        'signed_support_incidence_flat_prefix_append':all_('A r s M l T z',P('A','r','s','M','l','T'),F('A','r','s','M','S l','z'),exists('U',P('A','r','s','M','S l','U'),Q('T','U','S l'))),
        'signed_support_incidence_flat_prefix_exists':all_('A r s M l',T('0','A'),exists('T',P('A','r','s','M','l','T'))),
        'signed_support_incidence_from_flat_prefix':all_('A r s L M T',T('0','A'),P('A','r','s','M','L*(S M)','T'),incidence()),
        'signed_support_incidence_exists':all_('A r s L M',T('0','A'),exists('T',incidence())),
        'signed_support_incidence_row_lookup':all_('A r s L M T V i j z',incidence(),SL('T','V',row_origin,'1','M'),LT('i','L'),LT('j','M'),A('V','j','z'),E('A','r','s','i','j','z')),
        'signed_support_incidence_column_lookup':all_('A r s L M T V i j z',incidence(),SL('T','V',column_origin,'S M','L'),LT('i','L'),LT('j','M'),A('V','i','z'),E('A','r','s','i','j','z')),
        'signed_support_incidence_row_sum_value':all_('A B r s L M T i a z',support(),incidence(),LT('i','L'),A('A','i','a'),SS('T',row_origin,'1','M','z'),'z=a'),
        'signed_support_incidence_column_sum_value':all_('A B r s L M T j b z',support(),incidence(),LT('j','M'),A('B','j','b'),SS('T',column_origin,'S M','L','z'),'z=b'),
        'signed_support_incidence_row_sums_equal':all_('A B r s L M T R',support(),incidence(),RS('T','R','0','S M','1','L','M'),Q('A','R','L')),
        'signed_support_incidence_column_sums_equal':all_('A B r s L M T C',support(),incidence(),RS('T','C','0','1','S M','M','L'),Q('B','C','M')),
        'signed_support_reindex_sum_equal':all_('A B r s L M u v',support(),S('A','L','u'),S('B','M','v'),'u=v'),
        'signed_support_reindex_sum_exists':all_('A B r s L M',support(),exists('z',S('A','L','z'),S('B','M','z'))),
    }


def exact_ast(formula):
    return FormulaArena().freeze(_closed_formula(formula)).to_json()


@pytest.mark.parametrize('row',rows(),ids=lambda row:row.name)
def test_every_target_is_independently_expanded_without_candidate_builders(row):
    assert exact_ast(row.statement)==exact_ast(expected_statements()[row.name])


def test_exact_non_circular_topology_has_only_real_used_dependencies():
    assert len(rows())==25 and tuple(expected_statements())==tuple(row.name for row in rows())
    assert len(METRICS)==25 and sum(value[0] for value in METRICS)==2448
    assert sum(len(row.dependencies) for row in rows())==79
    assert sum(len(row.script) for row in rows())==1392
    available=set(core())
    for row in rows():
        assert row.name not in available
        assert len(row.dependencies)==len(set(row.dependencies))
        assert set(row.dependencies)<=available
        assert all(re.search(r'(?<![\w\'])'+re.escape(name)+r'(?![\w\'])','\n'.join(row.script)) for name in row.dependencies)
        assert not any(command.startswith(('use ','admit','sorry','DNE','ring')) for command in row.script)
        available.add(row.name)


@pytest.mark.parametrize('row',rows(),ids=lambda row:row.name)
def test_original_ha_body(row):
    try:
        receipt=replay_candidate_bodies((row,),core=core()|{item.name:item for item in rows()})[0]
        assert receipt.name==row.name and receipt.proof_nodes>0
        assert (receipt.proof_nodes,receipt.proof_objects,receipt.proof_depth)==METRICS[rows().index(row)]
        assert 0<receipt.proof_objects<=receipt.proof_nodes
        assert receipt.proof_depth<=256
    finally:
        gc.collect()


@pytest.mark.parametrize('row',rows(),ids=lambda row:row.name)
@pytest.mark.parametrize('kind',('false_target','missing_body'))
def test_false_or_absent_body_is_not_a_proof(row,kind):
    changed=replace(row,statement='0=1') if kind=='false_target' else replace(row,script=())
    with pytest.raises(CandidateBodyError):
        replay_candidate_bodies((changed,),core=core()|{item.name:item for item in rows()})
    gc.collect()


EDGES=tuple((row,dependency) for row in rows() for dependency in row.dependencies)


@pytest.mark.parametrize('row,dependency',EDGES,ids=lambda value:value.name if hasattr(value,'name') else value)
def test_dropped_dependency_is_rejected(row,dependency):
    changed=replace(row,dependencies=tuple(name for name in row.dependencies if name!=dependency))
    with pytest.raises(CandidateBodyError):
        replay_candidate_bodies((changed,),core=core()|{item.name:item for item in rows()})
    gc.collect()


@pytest.mark.parametrize('row,dependency',EDGES,ids=lambda value:value.name if hasattr(value,'name') else value)
def test_poisoned_dependency_is_rejected(row,dependency):
    available=core()|{item.name:item for item in rows()}
    available[dependency]=replace(available[dependency],statement='0=1')
    with pytest.raises(CandidateBodyError):
        replay_candidate_bodies((row,),core=available)
    gc.collect()


SURFACES=(
    (candidate.signed_support_reindex_relation,('A','B','r','s','L','M'),expected_support),
    (candidate.signed_support_incidence_entry_relation,('A','r','s','i','j','z'),expected_incidence_entry),
    (candidate.signed_support_incidence_flat_entry_relation,('A','r','s','M','k','z'),expected_flat_entry),
    (candidate.signed_support_incidence_flat_prefix_relation,('A','r','s','M','L','T'),expected_flat_prefix),
    (candidate.signed_support_incidence_relation,('A','r','s','L','M','T'),expected_incidence),
)
CONTEXT=('A','B','r','s','L','M','T','i','j','k','z','unused')


@pytest.mark.parametrize('builder,arguments,expected',SURFACES)
@pytest.mark.parametrize('mode',('identifiers','compound','large','zero','repeated'))
def test_public_graphs_are_exact_conservative_expansions(builder,arguments,expected,mode):
    values=arguments
    if mode=='compound':values=tuple(f'{value}+1' if index%2==0 else f'{value}*{value}' for index,value in enumerate(arguments))
    if mode=='large':values=('12345678901234567890123456789012345678901234567890',*arguments[1:])
    if mode=='zero':values=('0',)*len(arguments)
    if mode=='repeated':values=('A',)*len(arguments)
    actual=builder(*values,tag='contract',variables=CONTEXT)
    independent=expected(*values,'independent')
    _assert_same_ast(parse_formula_in_context(actual,list(CONTEXT)),parse_formula_in_context(independent,list(CONTEXT)))


@pytest.mark.parametrize('builder,arguments,expected',SURFACES)
def test_every_generated_binder_rejects_capture_even_as_an_unused_context_variable(builder,arguments,expected):
    expanded=builder(*arguments,tag='capture',variables=CONTEXT)
    binders={name for clause in re.findall(r'\b(?:forall|exists)\s+([^.]*)\.',expanded) for name in clause.split()}
    assert binders and not binders.intersection(CONTEXT)
    for name in binders:
        with pytest.raises(ValueError):
            builder(*arguments,tag='capture',variables=CONTEXT+(name,))


@pytest.mark.parametrize('builder,arguments,expected',SURFACES)
@pytest.mark.parametrize('mutation',('unknown_term','syntax','empty_context','duplicate_context','missing_context','reserved_tag','extra_argument'))
def test_malformed_definition_inputs_are_not_oracles(builder,arguments,expected,mutation):
    context,tag=CONTEXT,'bad'
    if mutation=='unknown_term':arguments=('not_declared',*arguments[1:])
    if mutation=='syntax':arguments=('A -> B',*arguments[1:])
    if mutation=='empty_context':context=()
    if mutation=='duplicate_context':context=CONTEXT+('A',)
    if mutation=='missing_context':context=CONTEXT[1:]
    if mutation=='reserved_tag':tag='forall'
    if mutation=='extra_argument':arguments=(*arguments,'0')
    with pytest.raises((ValueError,TypeError)):
        builder(*arguments,tag=tag,variables=context)


def test_all_statements_are_ast_distinct_from_3796_prior_rows_and_each_other():
    from peano_lab.library import editions_v31
    previous=editions_v31.ALPHA_CHECKED_SPECS
    assert len(previous)==len({row.name for row in previous})==3796
    buckets={}
    for row in rows():
        encoded=exact_ast(row.statement)
        key=sha256(encoded.encode()).digest()
        assert encoded not in buckets.setdefault(key,[])
        buckets[key].append(encoded)
    for row in previous:
        encoded=exact_ast(row.statement)
        assert encoded not in buckets.get(sha256(encoded.encode()).digest(),()),row.name
    # Digests select buckets; exact canonical parsed DAG bytes decide equality.


def beta_value(mapping,index):
    r,s=mapping
    modulus=1+(index+1)*s
    value=r%modulus
    quotient=r//modulus
    assert 0<=value<modulus and r==quotient*modulus+value
    return value


def support_clauses(source,target,mapping,L,M):
    left=[model_at(source,i) for i in range(L)]
    right=[model_at(target,j) for j in range(M)]
    active=[i for i,value in enumerate(left) if value!=0]
    images={i:beta_value(mapping,i) for i in active}
    preserve=all(images[i]<M and model_at(target,images[i])==left[i] for i in active)
    injective=len(set(images.values()))==len(images)
    cover=all(value==0 or any(images[i]==j and left[i]==value for i in active)
              for j,value in enumerate(right))
    return preserve,injective,cover


def check_actual_incidence(first,second,indices,offset,*,mapping_override=None):
    L,M=len(first),len(second)
    assert len(indices)==L
    source=model_table(first,offset=offset,endpoint=23)
    target=model_table(second,offset=offset+7,endpoint=-31)
    mapping=beta_stream((*indices,0)) if mapping_override is None else mapping_override
    assert tuple(beta_value(mapping,i) for i in range(L))==tuple(indices)
    assert support_clauses(source,target,mapping,L,M)==(True,True,True)
    W=M+1
    cells=[]
    for k in range(L*W+1):
        i,j=divmod(k,W)
        assert k==W*i+j and 0<=j<W
        value=decode_signed(model_at(source,i)) if j==beta_value(mapping,i) else 0
        cells.append(value)
    table=model_table(cells[:-1],offset=offset+11,endpoint=cells[-1])
    for k,value in enumerate(cells):
        assert model_at(table,k)==encode_signed(value)
    row_values=[]
    for i in range(L):
        actual=tuple(decode_signed(model_at(table,W*i+j)) for j in range(M))
        row=model_table(actual,offset=offset+13,endpoint=-17)
        result=actual_sum_trace(row,M)
        assert result==model_at(source,i)
        row_values.append(decode_signed(result))
    column_values=[]
    for j in range(M):
        actual=tuple(decode_signed(model_at(table,W*i+j)) for i in range(L))
        column=model_table(actual,offset=offset+19,endpoint=29)
        result=actual_sum_trace(column,L)
        assert result==model_at(target,j)
        column_values.append(decode_signed(result))
    R=model_table(row_values,offset=offset+23,endpoint=37)
    C=model_table(column_values,offset=offset+29,endpoint=-41)
    common=actual_sum_trace(source,L)
    assert common==actual_sum_trace(target,M)==actual_sum_trace(R,L)==actual_sum_trace(C,M)
    assert model_at(table,L*W)==encode_signed(23)  # Actual nonzero, unsummed endpoint.
    return source,target,mapping,table,common


EXAMPLES=(
    ((),(),()),
    ((),(0,0,0),()),
    ((0,0,0),(),(99,7,0)),
    ((3,),(3,),(0,)),
    ((-4,),(-4,),(0,)),
    ((0,3,0,-2),(-2,0,3,0,0),(99,2,0,0)),
    ((5,0,5),(5,5),(1,1,0)),
    ((-2,0,7),(7,0,0,-2),(3,3,0)),
)


@pytest.mark.parametrize('first,second,indices',EXAMPLES)
@pytest.mark.parametrize('offset',(0,9))
def test_actual_beta_incidence_and_both_fold_traces_cover_empty_and_inactive_collisions(first,second,indices,offset):
    check_actual_incidence(first,second,indices,offset)


@pytest.mark.parametrize('seed',range(12))
def test_actual_random_signed_support_maps_preserve_values_not_representations(seed):
    rng=random.Random(seed)
    L,M=rng.randrange(5),rng.randrange(6)
    count=rng.randrange(min(L,M)+1)
    source_indices=rng.sample(range(L),count)
    target_indices=rng.sample(range(M),count)
    first=[0]*L
    second=[0]*M
    indices=[rng.randrange(M+10) for _ in range(L)]
    for i,j in zip(source_indices,target_indices,strict=True):
        value=rng.choice((-7,-3,-1,1,4,9))
        first[i]=second[j]=value
        indices[i]=j
    left=check_actual_incidence(first,second,indices,3)
    right=check_actual_incidence(first,second,indices,17)
    assert left[0][0]!=right[0][0] and left[0][1]!=right[0][1]
    assert left[1][0]!=right[1][0] and left[1][1]!=right[1][1]
    assert left[3][0]!=right[3][0] and left[4]==right[4]


@pytest.mark.parametrize('first,second,indices,clauses',(
    ((1,1),(1,),(0,0),(True,False,True)),
    ((1,),(1,1),(0,),(True,True,False)),
    ((1,),(),(0,),(False,True,True)),
    ((1,),(0,),(0,),(False,True,True)),
))
def test_independent_counterexamples_expose_missing_support_obligations(first,second,indices,clauses):
    source=model_table(first,offset=3,endpoint=19)
    target=model_table(second,offset=7,endpoint=1)
    mapping=beta_stream((*indices,0))
    assert support_clauses(source,target,mapping,len(first),len(second))==clauses
    assert actual_sum_trace(source,len(first))!=actual_sum_trace(target,len(second))


def test_native_beta_image_one_is_natural_index_one_not_signed_minus_one():
    source,target,mapping,_,_=check_actual_incidence((7,),(0,7),(1,),5)
    assert beta_value(mapping,0)==1
    assert decode_signed(1)==-1
    assert model_at(source,0)==model_at(target,1)==encode_signed(7)


def test_native_beta_scale_zero_is_valid_with_inactive_collisions():
    check_actual_incidence((-7,0,0),(-7,),(0,0,0),5,mapping_override=(999,0))


@pytest.mark.parametrize('length,position,value',(
    (1,0,0),(1,0,-3),(3,0,5),(3,1,-4),(3,2,7),(4,1,0),(4,3,-9),
))
def test_actual_single_spike_values_include_both_boundaries_zero_and_negatives(length,position,value):
    values=[0]*length
    values[position]=value
    first=model_table(values,offset=5,endpoint=101)
    second=model_table(values,offset=13,endpoint=-103)
    assert first[0]!=second[0]
    assert actual_sum_trace(first,length)==actual_sum_trace(second,length)==encode_signed(value)


@pytest.mark.parametrize('length,position',((0,0),(1,1),(2,4)))
def test_a_spike_outside_the_window_cannot_determine_its_sum(length,position):
    values=[0]*(position+1)
    values[position]=7
    table=model_table(values,offset=11,endpoint=29)
    assert not position<length
    assert model_at(table,position)==encode_signed(7)
    assert actual_sum_trace(table,length)==0
