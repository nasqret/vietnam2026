"""Actual unit constructors: ordinary HA, exact graphs, and hostile inputs.

Finite arithmetic models below are diagnostics, never proof certificates.
Original-kernel body checks leave declared dependencies as hypotheses; the
separate complete support-cone HA/Lean check is still required for closure.
"""

from dataclasses import fields, is_dataclass, replace
from functools import lru_cache
import gc
import math
from pathlib import Path
import re
import sys

import pytest

ROOT=Path(__file__).resolve().parents[3]
if str(ROOT/'scripts') not in sys.path:
    sys.path.insert(0,str(ROOT/'scripts'))

from constructive_dirichlet_support import previous_rows, statement_duplicates
from peano_lab.library import campaign_bottom_layer_closure as closure
from peano_lab.library import dirichlet_convolution_candidate as convolution
from peano_lab.library import dirichlet_commutativity_candidate as commutativity
from peano_lab.library import signed_finite_support_candidate as finite_support
from peano_lab.library import dirichlet_units_candidate as candidate
from peano_lab.library.candidate_validation import CandidateBodyError, replay_candidate_bodies
from peano_lab.library.divisor_mask_candidate import _divisor_sum, _positive_equal
from peano_lab.library.divisor_sum_table_candidate import _table, _table_at
from peano_lab.library.prime_valuation_support_candidate import _and, _le, _lt
from peano_lab.library.theorems import TheoremSpec, _closed_formula
from peano_lab.kernel.formulas import parse_formula_in_context, pretty_formula


@lru_cache(maxsize=1)
def core():
    inherited=(*closure.parent_snapshot().specs,*previous_rows())
    assert len(inherited)==len({row.name for row in inherited})==3643
    assert closure.PARENT_CATALOG_SHA256=='ac7111ec14ff07bf899238ed465de337e6d76e9343384947022360dc7e65d9f7'
    current=(*convolution.make_dirichlet_convolution_candidate_theorems(TheoremSpec),
             *finite_support.make_signed_finite_support_candidate_theorems(TheoremSpec),
             *commutativity.make_dirichlet_commutativity_candidate_theorems(TheoremSpec))
    return {row.name:row for row in (*inherited,*current)}


@lru_cache(maxsize=1)
def rows():
    return candidate.make_dirichlet_units_candidate_theorems(TheoremSpec)


@pytest.mark.parametrize('row',rows(),ids=lambda row:row.name)
def test_original_kernel_body(row):
    try:
        checked=replay_candidate_bodies((row,),core=core()|{r.name:r for r in rows()})[0]
        assert checked.name==row.name
        assert checked.proof_nodes>0 and checked.proof_depth<=256
    except CandidateBodyError as error:
        pytest.fail(str(error),pytrace=False)
    finally:
        gc.collect()


EXPECTED_NAMES = (
    'dirichlet_constant_one_table_value',
    'dirichlet_kronecker_delta_table_one_value',
    'dirichlet_kronecker_delta_table_other_value',
    'dirichlet_kronecker_delta_value_exists',
    'dirichlet_constant_one_table_append',
    'dirichlet_kronecker_delta_table_append',
    'dirichlet_constant_one_table_exists',
    'dirichlet_kronecker_delta_table_exists',
    'dirichlet_constant_one_table_reencoding',
    'dirichlet_constant_one_table_positive_unique',
    'dirichlet_kronecker_delta_table_reencoding',
    'dirichlet_kronecker_delta_table_positive_unique',
    'dirichlet_delta_right_entry_before_input',
    'dirichlet_delta_right_last_entry',
    'dirichlet_delta_right_sum_value',
    'dirichlet_delta_right_sum',
    'dirichlet_delta_right_table',
    'dirichlet_delta_left_table',
    'dirichlet_delta_unit_exists',
    'dirichlet_constant_one_entry_to_divisor_mask',
    'dirichlet_constant_one_entry_from_divisor_mask',
    'dirichlet_constant_one_prefix_to_divisor_mask',
    'dirichlet_constant_one_prefix_from_divisor_mask',
    'dirichlet_constant_one_sum_iff',
    'dirichlet_constant_one_realizes_divisor_sum',
)


def test_inventory_is_ordered_acyclic_and_uses_every_declared_dependency():
    assert tuple(row.name for row in rows()) == EXPECTED_NAMES
    seen=set(core())
    assert len(seen) <= 3743
    for row in rows():
        assert type(row) is TheoremSpec and row.name not in seen
        assert len(set(row.dependencies)) == len(row.dependencies)
        assert set(row.dependencies) <= seen
        referenced={command.split()[1] for command in row.script
                    if command.startswith(('apply ','specialize '))}
        assert set(row.dependencies) <= referenced
        assert all(command.split()[0] not in {'admit','sorry','dne','classical','trust','oracle'}
                   for command in row.script)
        _closed_formula(row.statement)
        seen.add(row.name)


def test_novelty_against_all_3643_prior_statements_and_current_dependencies():
    current=(*convolution.make_dirichlet_convolution_candidate_theorems(TheoremSpec),
             *finite_support.make_signed_finite_support_candidate_theorems(TheoremSpec),
             *commutativity.make_dirichlet_commutativity_candidate_theorems(TheoremSpec),
             *rows())
    own=set(EXPECTED_NAMES)
    assert not tuple(pair for pair in statement_duplicates(current) if pair[0] in own)


@pytest.mark.parametrize('row',rows(),ids=lambda row:row.name)
def test_replacing_an_actual_body_with_refl_is_rejected(row):
    altered=replace(row,script=('refl',))
    _must_reject(altered,core()|{r.name:r for r in rows()})
    gc.collect()


def _must_reject(row,table):
    """Fail concisely instead of rendering a many-thousand-row core on error."""
    try:
        replay_candidate_bodies((row,),core=table)
    except CandidateBodyError:
        return
    except Exception as error:
        pytest.fail(f'{row.name}: unexpected {type(error).__name__}: {error}',pytrace=False)
    pytest.fail(f'{row.name}: the original kernel accepted a hostile candidate',pytrace=False)


@pytest.mark.parametrize('name,dependency',tuple((row.name,dependency) for row in rows() for dependency in row.dependencies))
@pytest.mark.parametrize('attack',('remove','change_statement'))
def test_actual_body_rejects_missing_or_forged_dependency(name,dependency,attack):
    row=next(row for row in rows() if row.name==name)
    table=core()|{r.name:r for r in rows()}
    if attack=='remove':
        altered=replace(row,dependencies=tuple(item for item in row.dependencies if item!=dependency))
    else:
        altered=row
        table[dependency]=replace(table[dependency],statement='0=0')
    _must_reject(altered,table)
    gc.collect()


def _expected_one(N,U,tag):
    return _and(_table(N,U,tag+'data'),
        f"forall i z. ~(i=0) -> ({_le('i',N,tag+'bound')}) -> ({_table_at(U,'i','z',tag+'value')}) -> z=2")


def _expected_delta(N,E,tag):
    return _and(_table(N,E,tag+'data'),
        f"forall i z. ~(i=0) -> ({_le('i',N,tag+'bound')}) -> ({_table_at(E,'i','z',tag+'value')}) -> "
        '((i=1 -> z=2) /\\ (~(i=1) -> z=0))')


BUILDERS = (
    ('one',candidate.dirichlet_constant_one_table_relation,_expected_one),
    ('delta',candidate.dirichlet_kronecker_delta_table_relation,_expected_delta),
)


def _same_ast(left,right):
    """Exact structural equality without expanding shared numeral subtrees."""
    pending,seen=[(left,right)],set()
    while pending:
        a,b=pending.pop()
        assert type(a) is type(b)
        pair=id(a),id(b)
        if pair in seen:
            continue
        seen.add(pair)
        if is_dataclass(a):
            pending.extend((getattr(a,field.name),getattr(b,field.name)) for field in fields(a))
        else:
            assert a==b


@pytest.mark.parametrize('label,builder,expected',BUILDERS,ids=('one','delta'))
@pytest.mark.parametrize('arguments',(('N','F'),('0','F'),('S (N+F)','(N*F)+1'),
                                   (str(2**96+17),'F+N'),('N',str(2**96+17))),
                         ids=('variables','empty','compound','large-bound','large-table-code'))
def test_public_graph_is_exact_canonical_table_and_positive_value_data(label,builder,expected,arguments):
    context=['N','F']
    actual=builder(*arguments,tag='explicit',variables=tuple(context))
    literal=expected(*arguments,'expected')
    parsed=parse_formula_in_context(actual,context)
    _same_ast(parsed,parse_formula_in_context(literal,context))
    _same_ast(parse_formula_in_context(pretty_formula(parsed,context),context),parsed)


def _generated_binder_cases():
    result=[]
    for label,builder,_ in BUILDERS:
        formula=builder('N','F',tag='capture',variables=('N','F'))
        binders={word for clause in re.findall(r'\b(?:forall|exists)\s+([^.]*)\.',formula)
                 for word in clause.split()}
        assert len(binders)>20
        result.extend((label,builder,binder) for binder in sorted(binders))
    return tuple(result)


@pytest.mark.parametrize('label,builder,binder',_generated_binder_cases(),
                         ids=lambda item:item if isinstance(item,str) else item.__name__)
def test_every_generated_binder_rejects_declared_context_capture(label,builder,binder):
    with pytest.raises(ValueError,match='captures'):
        builder('N','F',tag='capture',variables=('N','F',binder))
    with pytest.raises(ValueError,match='captures'):
        builder('N+'+binder,'F',tag='capture',variables=('N','F',binder))


@pytest.mark.parametrize('label,builder,expected',BUILDERS,ids=('one','delta'))
@pytest.mark.parametrize('tag',('', 'two words','a-b','a.b','x;exists z'))
def test_malformed_binder_tags_fail_closed(label,builder,expected,tag):
    with pytest.raises((TypeError,ValueError)):
        builder('N','F',tag=tag,variables=('N','F'))


@pytest.mark.parametrize('label,builder,expected',BUILDERS,ids=('one','delta'))
@pytest.mark.parametrize('variables',((),['N','F'],('N','N'),('N',),('N','F','bad name')))
def test_malformed_contexts_fail_closed(label,builder,expected,variables):
    with pytest.raises((TypeError,ValueError)):
        builder('N','F',tag='guard',variables=variables)


@pytest.mark.parametrize('label,builder,expected',BUILDERS,ids=('one','delta'))
@pytest.mark.parametrize('term',('missing','-1','N/F','N; forall q. q=0',None,True))
def test_malformed_or_free_terms_fail_closed(label,builder,expected,term):
    with pytest.raises((TypeError,ValueError)):
        builder(term,'F',tag='guard',variables=('N','F'))


def _independent_endpoint_statements():
    one=_expected_one('N','U','contract_one')
    delta=_expected_delta('N','E','contract_delta')
    table=_table('N','F','contract_source')
    at=_table_at('F','n','a','contract_value')
    bound=_le('n','N','contract_bound')
    right=convolution._convolution_table('N','F','E','F','contract_right')
    left=convolution._convolution_table('N','E','F','F','contract_left')
    conv=convolution._convolution('F','U','n','z','contract_convolution')
    divisor=_divisor_sum('F','n','z','contract_divisor')
    iff=_and(f'({conv})->({divisor})',f'({divisor})->({conv})')
    return {
        'dirichlet_constant_one_table_exists':f"forall N w. exists U. ({one}) /\\ ({_table_at('U','0','w','contract_zero')})",
        'dirichlet_kronecker_delta_table_exists':f"forall N w. exists E. ({delta}) /\\ ({_table_at('E','0','w','contract_zero')})",
        'dirichlet_delta_right_entry_before_input':f"forall N F E n d z. ({delta})->~(n=0)->({bound})->({_lt('d','n','contract_before')})->({convolution._entry('F','E','n','d','z','contract_entry')})->z=0",
        'dirichlet_delta_right_last_entry':f"forall N F E n a. ({delta})->~(n=0)->({bound})->({at})->({convolution._entry('F','E','n','n','a','contract_last')})",
        'dirichlet_delta_right_sum_value':f"forall N F E n a z. ({delta})->({bound})->({at})->({convolution._convolution('F','E','n','z','contract_given')})->z=a",
        'dirichlet_delta_right_sum':f"forall N F E n a. ({table})->({delta})->~(n=0)->({bound})->({at})->({convolution._convolution('F','E','n','a','contract_actual')})",
        'dirichlet_delta_right_table':f'forall N F E. ({table})->({delta})->({right})',
        'dirichlet_delta_left_table':f'forall N F E. ({table})->({delta})->({left})',
        'dirichlet_delta_unit_exists':f'forall N F w. ({table})->exists E. '+_and(delta,_table_at('E','0','w','contract_zero'),right,left),
        'dirichlet_constant_one_sum_iff':f'forall N F U n z. ({table})->({one})->~(n=0)->({bound})->({iff})',
        'dirichlet_constant_one_realizes_divisor_sum':f'forall N F w. ({table})->exists U. '+_and(one,_table_at('U','0','w','contract_zero'),f'forall n z. ~(n=0)->({bound})->({iff})'),
    }


@pytest.mark.parametrize('name',tuple(_independent_endpoint_statements()))
def test_principal_statements_have_exact_constructive_and_domain_contracts(name):
    row=next(row for row in rows() if row.name==name)
    assert _closed_formula(row.statement)==_closed_formula(_independent_endpoint_statements()[name])


@pytest.mark.parametrize('attack',('zero_input','missing_delta','wrong_output','equal_zero_entries','wrong_transform_source'))
def test_actual_body_rejects_false_guard_or_output_strengthening(attack):
    table=_table('N','F','hostile_table')
    delta=_expected_delta('N','E','hostile_delta')
    if attack=='zero_input':
        name='dirichlet_delta_right_sum'
        statement=_independent_endpoint_statements()[name].replace('->~(n=0)','',1)
    elif attack=='missing_delta':
        name='dirichlet_delta_right_table'
        statement=f"forall N F E. ({table})->({_table('N','E','hostile_arbitrary')})->({convolution._convolution_table('N','F','E','F','hostile_unit')})"
    elif attack=='wrong_output':
        name='dirichlet_delta_left_table'
        statement=f"forall N F E. ({table})->({delta})->({convolution._convolution_table('N','E','F','E','hostile_output')})"
    elif attack=='equal_zero_entries':
        name='dirichlet_constant_one_table_positive_unique'
        statement=(f"forall N F G. ({_expected_one('N','F','hostile_first')})->({_expected_one('N','G','hostile_second')})->"
                   f"forall i a b. ({_le('i','N','hostile_bound')})->({_table_at('F','i','a','hostile_f')})->({_table_at('G','i','b','hostile_g')})->a=b")
    else:
        name='dirichlet_constant_one_sum_iff'
        actual=convolution._convolution('F','U','n','z','hostile_convolution')
        wrong=_divisor_sum('U','n','z','hostile_wrong_divisor')
        statement=(f"forall N F U n z. ({table})->({_expected_one('N','U','hostile_ones')})->~(n=0)->({_le('n','N','hostile_domain')})->"
                   +_and(f'({actual})->({wrong})',f'({wrong})->({actual})'))
    row=next(row for row in rows() if row.name==name)
    _must_reject(replace(row,statement=statement),core()|{r.name:r for r in rows()})
    gc.collect()


def _signed_code(integer):
    return 2*integer if integer>=0 else -2*integer-1


def _signed_value(code):
    if type(code) is not int or code<0:
        raise ValueError('not a natural signed code')
    return code//2 if code%2==0 else -(code//2+1)


def _pair(a,b):
    return (a+b)*(a+b+1)+2*b


def _unpair(code):
    if type(code) is not int or code<0 or code%2:
        raise ValueError('not a pairing code')
    value=code//2
    diagonal=(math.isqrt(8*value+1)-1)//2
    second=value-diagonal*(diagonal+1)//2
    return diagonal-second,second


def _beta_encode(values):
    scale=math.factorial(len(values))*(max(values,default=0)+1)
    moduli=[1+(i+1)*scale for i in range(len(values))]
    product=math.prod(moduli)
    encoded=sum(value*(product//modulus)*pow(product//modulus,-1,modulus)
                for value,modulus in zip(values,moduli))%product
    assert all(encoded%modulus==value for modulus,value in zip(moduli,values))
    return encoded,scale


def _encode_table(values,*,offset=0):
    positive=[max(value,0)+offset+i%2 for i,value in enumerate(values)]
    negative=[max(-value,0)+offset+i%2 for i,value in enumerate(values)]
    pb,pc=_beta_encode(positive)
    nb,nc=_beta_encode(negative)
    return _pair(_pair(pb,pc),_pair(nb,nc))


def _components_at(code,index):
    positive,negative=_unpair(code)
    pb,pc=_unpair(positive)
    nb,nc=_unpair(negative)
    return pb%(1+(index+1)*pc),nb%(1+(index+1)*nc)


def _at_model(code,index):
    positive,negative=_components_at(code,index)
    return _signed_code(positive-negative)


def _table_model(code):
    try:
        _components_at(code,0)
    except ValueError:
        return False
    return True


def _one_model(N,code):
    return _table_model(code) and all(_at_model(code,i)==2 for i in range(1,N+1))


def _delta_model(N,code):
    return _table_model(code) and all(_at_model(code,i)==(2 if i==1 else 0) for i in range(1,N+1))


def _signed_fold_model(code,length):
    return _signed_code(sum(_signed_value(_at_model(code,i)) for i in range(length)))


def _convolution_model(F,G,n):
    if n<=0:
        raise ValueError('convolution is positive-input only')
    values=[0]+[(_signed_value(_at_model(F,d))*_signed_value(_at_model(G,n//d))
                 if n%d==0 else 0) for d in range(1,n+1)]
    mask=_encode_table(values,offset=3)
    assert all(_at_model(mask,d)==_signed_code(value) for d,value in enumerate(values))
    return _signed_fold_model(mask,n+1)


@pytest.mark.parametrize('N',range(9))
@pytest.mark.parametrize('zero',(-9,0,1,37))
def test_real_beta_constructors_include_empty_and_preserve_arbitrary_zero(N,zero):
    U=_encode_table([zero]+[1]*N)
    E=_encode_table([zero]+[1 if i==1 else 0 for i in range(1,N+1)])
    assert _one_model(N,U) and _delta_model(N,E)
    assert _at_model(U,0)==_at_model(E,0)==_signed_code(zero)
    if N:
        assert _at_model(U,1)==_at_model(E,1)==2
    assert not _one_model(N,1) and not _delta_model(N,1)


@pytest.mark.parametrize('N',range(1,9))
@pytest.mark.parametrize('offset',(0,4))
def test_actual_signed_folds_obey_both_units_and_existing_divisor_sum(N,offset):
    values=[-19]+[(-1)**i*(3*i+1) for i in range(1,N+1)]
    F=_encode_table(values,offset=offset)
    E=_encode_table([41]+[1 if i==1 else 0 for i in range(1,N+1)],offset=offset+1)
    U=_encode_table([-73]+[1]*N,offset=offset+2)
    for n in range(1,N+1):
        assert _convolution_model(F,E,n)==_convolution_model(E,F,n)==_at_model(F,n)
        divisor_mask=_encode_table([0]+[values[d] if n%d==0 else 0 for d in range(1,n+1)])
        assert _convolution_model(F,U,n)==_signed_fold_model(divisor_mask,n+1)
        assert _convolution_model(U,F,n)==_signed_fold_model(divisor_mask,n+1)


@pytest.mark.parametrize('N',(0,1,2,7))
@pytest.mark.parametrize('kind',('one','delta'))
def test_positive_extensionality_does_not_identify_codes_components_or_zero(N,kind):
    values=[1 if kind=='one' or i==1 else 0 for i in range(1,N+1)]
    F=_encode_table([-11]+values,offset=0)
    G=_encode_table([29]+values,offset=5)
    graph=_one_model if kind=='one' else _delta_model
    assert F!=G and _at_model(F,0)!=_at_model(G,0)
    assert graph(N,F) and graph(N,G)
    for i in range(1,N+1):
        assert _components_at(F,i)!=_components_at(G,i)
        assert _at_model(F,i)==_at_model(G,i)


def test_positive_domain_and_finite_bound_guards_are_mathematically_necessary():
    F=_encode_table([-3,5,3])
    U=E=_encode_table([19,1,7])
    assert _one_model(1,U) and _delta_model(1,E)
    assert not _one_model(2,U) and not _delta_model(2,E)
    assert _convolution_model(F,E,2)!=_at_model(F,2)
    assert _signed_value(_convolution_model(F,U,2))!=5+3
    with pytest.raises(ValueError,match='positive-input'):
        _convolution_model(F,E,0)
    assert _one_model(0,0) and _delta_model(0,0)
    assert not _one_model(1,0) and not _delta_model(1,0)


def test_large_signed_values_reencoding_and_singleton_boundary():
    large=2**130+19
    F=_encode_table([large,-large],offset=large)
    E=_encode_table([-large,1],offset=large+1)
    U=_encode_table([large+1,1],offset=large+2)
    assert _convolution_model(F,E,1)==_at_model(F,1)==_signed_code(-large)
    assert _convolution_model(F,U,1)==_signed_code(-large)
